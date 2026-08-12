"""
Batch Execution Service
-----------------------
Handles creation, execution, progress tracking, cancellation, and retry
of batch model execution jobs.

Each batch runs all active teams' latest model submissions against one or more matches.
"""
import uuid
import pickle
from datetime import datetime, timezone

from app.model_execution.services.model_compat import safe_load
from typing import Optional

from sqlalchemy.orm import Session

from app.model_execution.models.batch_execution import BatchExecutionModel, BatchJobModel
from app.models.model_submission import ModelSubmissionModel
from app.models.team import TeamModel
from app.models.match import MatchModel


class BatchExecutionService:

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover_latest_models(self) -> list[dict]:
        """Return the latest active model submission for every team that has one."""
        # Get all active teams
        teams = self.db.query(TeamModel).filter(TeamModel.is_active.is_(True)).all()
        result = []
        for team in teams:
            submission = (
                self.db.query(ModelSubmissionModel)
                .filter(
                    ModelSubmissionModel.team_id == team.id,
                    ModelSubmissionModel.is_active.is_(True),
                )
                .order_by(ModelSubmissionModel.uploaded_at.desc())
                .first()
            )
            if submission:
                result.append({
                    "team": {"id": str(team.id), "name": team.name, "code": team.team_id},
                    "latest_model": {
                        "id": str(submission.id),
                        "original_filename": submission.file_name,
                        "file_path": submission.file_path,
                    },
                    "upload_time": submission.uploaded_at.isoformat(),
                })
        return result

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_batch(self, match_ids: list[str]) -> dict:
        """Create a new batch with jobs for every (team × match) combination."""
        # Resolve matches
        matches = []
        for mid in match_ids:
            try:
                m_uuid = uuid.UUID(mid)
                match = self.db.query(MatchModel).filter(MatchModel.id == m_uuid).first()
            except ValueError:
                match = None
            if match:
                matches.append(match)

        if not matches:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="No valid matches found in provided match_ids.")

        # Discover teams with active models
        teams_with_models = self.discover_latest_models()
        if not teams_with_models:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="No teams with active model submissions found.")

        total_jobs = len(teams_with_models) * len(matches)

        batch = BatchExecutionModel(
            overall_status="PENDING",
            total_jobs=total_jobs,
            pending_jobs=total_jobs,
            completed_jobs=0,
            failed_jobs=0,
        )
        self.db.add(batch)
        self.db.flush()  # get batch.id

        for tw in teams_with_models:
            team_id = uuid.UUID(tw["team"]["id"])
            model_submission_id = uuid.UUID(tw["latest_model"]["id"])
            for match in matches:
                job = BatchJobModel(
                    batch_id=batch.id,
                    team_id=team_id,
                    match_id=match.id,
                    model_submission_id=model_submission_id,
                    status="PENDING",
                )
                self.db.add(job)

        self.db.commit()
        self.db.refresh(batch)
        return self._batch_to_dict(batch)

    # ------------------------------------------------------------------
    # Execute (async trigger)
    # ------------------------------------------------------------------

    def execute_batch(self, batch_id: str) -> dict:
        """Trigger async execution of all pending jobs in a batch."""
        batch = self._get_batch_or_404(batch_id)
        if batch.overall_status in ("RUNNING",):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Batch is already running.")

        batch.overall_status = "RUNNING"
        batch.started_at = datetime.now(timezone.utc)
        self.db.commit()

        # Run in a background thread (best-effort — no celery required)
        import threading
        t = threading.Thread(target=self._run_batch_jobs, args=(batch.id,), daemon=True)
        t.start()

        return self._batch_to_dict(batch)

    def _run_batch_jobs(self, batch_id: uuid.UUID):
        """Execute all PENDING jobs in the batch sequentially (background thread)."""
        from app.database.session import SessionLocal
        db = SessionLocal()
        try:
            batch = db.query(BatchExecutionModel).filter(BatchExecutionModel.id == batch_id).first()
            if not batch:
                return

            pending_jobs = (
                db.query(BatchJobModel)
                .filter(BatchJobModel.batch_id == batch_id, BatchJobModel.status == "PENDING")
                .all()
            )

            for job in pending_jobs:
                # Re-check batch status — may have been cancelled
                db.refresh(batch)
                if batch.overall_status == "CANCELLED":
                    break

                job.status = "RUNNING"
                job.started_at = datetime.now(timezone.utc)
                db.commit()

                try:
                    self._execute_job(db, job)
                    job.status = "COMPLETED"
                    batch.completed_jobs += 1
                    batch.pending_jobs = max(0, batch.pending_jobs - 1)
                except Exception as exc:
                    job.status = "FAILED"
                    job.error_message = str(exc)
                    batch.failed_jobs += 1
                    batch.pending_jobs = max(0, batch.pending_jobs - 1)
                finally:
                    job.completed_at = datetime.now(timezone.utc)
                    db.commit()

            # Determine final batch status
            db.refresh(batch)
            if batch.overall_status == "CANCELLED":
                pass  # already set
            elif batch.failed_jobs > 0 and batch.completed_jobs == 0:
                batch.overall_status = "FAILED"
            elif batch.failed_jobs > 0:
                batch.overall_status = "COMPLETED"  # partially succeeded
            else:
                batch.overall_status = "COMPLETED"
            batch.completed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            try:
                batch = db.query(BatchExecutionModel).filter(BatchExecutionModel.id == batch_id).first()
                if batch:
                    batch.overall_status = "FAILED"
                    batch.completed_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    def _execute_job(self, db: Session, job: BatchJobModel):
        """Run a single job: load model → predict → save prediction."""
        # Get model submission
        submission = db.query(ModelSubmissionModel).filter(
            ModelSubmissionModel.id == job.model_submission_id
        ).first()
        if not submission:
            raise ValueError(f"Model submission {job.model_submission_id} not found")

        # Get match
        match = db.query(MatchModel).filter(MatchModel.id == job.match_id).first()
        if not match:
            raise ValueError(f"Match {job.match_id} not found")

        # Load model
        import os
        if not os.path.exists(submission.file_path):
            raise FileNotFoundError(f"Model file not found: {submission.file_path}")

        with open(submission.file_path, "rb") as f:
            model = safe_load(f)

        if not hasattr(model, "predict"):
            raise AttributeError("Loaded model object has no 'predict' method")

        # Run prediction
        import pandas as pd
        import numpy as np
        import scipy
        from scipy import stats
        import xgboost as xgb
        import lightgbm as lgb
        import sklearn
        import math

        model_input = {
            "home_team": match.home_team_name,
            "away_team": match.away_team_name,
        }
        model_output = model.predict(model_input)

        # Serialize output to prediction payload
        from app.model_execution.services.model_serializer import ModelSerializer
        serializer = ModelSerializer()
        payload = serializer.serialize_output(
            model_output=model_output,
            team_id=job.team_id,
            match_id=job.match_id,
        )

        # Save prediction
        from app.services.prediction_service import PredictionService
        pred_service = PredictionService(db)
        result = pred_service.save_prediction(payload)

        # Link prediction_id to job
        if result.get("status") in ("accepted", "duplicate"):
            from app.models.prediction import PredictionModel
            pred = db.query(PredictionModel).filter(
                PredictionModel.team_id == job.team_id,
                PredictionModel.match_id == job.match_id,
            ).first()
            if pred:
                job.prediction_id = pred.id

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    def get_batch_progress(self, batch_id: str) -> dict:
        batch = self._get_batch_or_404(batch_id)
        jobs = (
            self.db.query(BatchJobModel)
            .filter(BatchJobModel.batch_id == batch.id)
            .all()
        )

        total = batch.total_jobs or len(jobs)
        completed = sum(1 for j in jobs if j.status == "COMPLETED")
        failed = sum(1 for j in jobs if j.status == "FAILED")
        running = sum(1 for j in jobs if j.status == "RUNNING")
        pending = sum(1 for j in jobs if j.status == "PENDING")
        progress_pct = (completed / total * 100) if total > 0 else 0

        # Re-sync counts on batch
        batch.completed_jobs = completed
        batch.failed_jobs = failed
        batch.pending_jobs = pending
        self.db.commit()

        current_running_job = None
        running_jobs = [j for j in jobs if j.status == "RUNNING"]
        if running_jobs:
            rj = running_jobs[0]
            current_running_job = self._job_to_dict_detail(rj)

        return {
            "batch_summary": {
                "id": str(batch.id),
                "overall_status": batch.overall_status,
                "total_jobs": total,
                "completed_jobs": completed,
                "failed_jobs": failed,
                "pending_jobs": pending,
                "created_at": batch.created_at.isoformat(),
                "started_at": batch.started_at.isoformat() if batch.started_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            },
            "progress_percent": round(progress_pct, 1),
            "current_running_job": current_running_job,
            "jobs": [self._job_to_dict_detail(j) for j in jobs],
        }

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_batches(self) -> dict:
        batches = (
            self.db.query(BatchExecutionModel)
            .order_by(BatchExecutionModel.created_at.desc())
            .limit(50)
            .all()
        )
        return {"batches": [self._batch_to_dict(b) for b in batches]}

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    def cancel_batch(self, batch_id: str) -> dict:
        batch = self._get_batch_or_404(batch_id)
        if batch.overall_status in ("COMPLETED", "CANCELLED"):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Batch is already {batch.overall_status}.")

        batch.overall_status = "CANCELLED"
        batch.completed_at = datetime.now(timezone.utc)

        # Mark pending jobs as cancelled
        pending_jobs = (
            self.db.query(BatchJobModel)
            .filter(BatchJobModel.batch_id == batch.id, BatchJobModel.status == "PENDING")
            .all()
        )
        for job in pending_jobs:
            job.status = "CANCELLED"

        self.db.commit()
        return self._batch_to_dict(batch)

    # ------------------------------------------------------------------
    # Retry batch
    # ------------------------------------------------------------------

    def retry_batch(self, batch_id: str, force_all: bool = False) -> dict:
        batch = self._get_batch_or_404(batch_id)

        # Determine which jobs to reset
        if force_all:
            target_statuses = ("FAILED", "CANCELLED", "COMPLETED", "PENDING")
        else:
            target_statuses = ("FAILED", "CANCELLED")

        jobs_to_retry = (
            self.db.query(BatchJobModel)
            .filter(BatchJobModel.batch_id == batch.id, BatchJobModel.status.in_(target_statuses))
            .all()
        )

        for job in jobs_to_retry:
            job.status = "PENDING"
            job.error_message = None
            job.started_at = None
            job.completed_at = None

        # Re-tally
        all_jobs = self.db.query(BatchJobModel).filter(BatchJobModel.batch_id == batch.id).all()
        batch.total_jobs = len(all_jobs)
        batch.pending_jobs = sum(1 for j in all_jobs if j.status == "PENDING")
        batch.completed_jobs = sum(1 for j in all_jobs if j.status == "COMPLETED")
        batch.failed_jobs = sum(1 for j in all_jobs if j.status == "FAILED")
        batch.overall_status = "PENDING"
        batch.completed_at = None
        self.db.commit()

        # Kick off execution
        return self.execute_batch(batch_id)

    # ------------------------------------------------------------------
    # Retry single job
    # ------------------------------------------------------------------

    def retry_job(self, job_id: str) -> dict:
        try:
            job_uuid = uuid.UUID(job_id)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid job ID")

        job = self.db.query(BatchJobModel).filter(BatchJobModel.id == job_uuid).first()
        if not job:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Job not found")

        job.status = "PENDING"
        job.error_message = None
        job.started_at = None
        job.completed_at = None

        # Re-tally batch
        batch = job.batch
        all_jobs = self.db.query(BatchJobModel).filter(BatchJobModel.batch_id == batch.id).all()
        batch.pending_jobs = sum(1 for j in all_jobs if j.status == "PENDING")
        batch.failed_jobs = sum(1 for j in all_jobs if j.status == "FAILED")
        batch.completed_jobs = sum(1 for j in all_jobs if j.status == "COMPLETED")
        batch.overall_status = "PENDING"
        batch.completed_at = None
        self.db.commit()

        # Kick off execution for the batch (will only run PENDING jobs)
        return self.execute_batch(str(batch.id))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_batch_or_404(self, batch_id: str) -> BatchExecutionModel:
        try:
            batch_uuid = uuid.UUID(batch_id)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid batch ID")
        batch = self.db.query(BatchExecutionModel).filter(BatchExecutionModel.id == batch_uuid).first()
        if not batch:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Batch not found")
        return batch

    def _batch_to_dict(self, batch: BatchExecutionModel) -> dict:
        return {
            "id": str(batch.id),
            "overall_status": batch.overall_status,
            "total_jobs": batch.total_jobs,
            "completed_jobs": batch.completed_jobs,
            "failed_jobs": batch.failed_jobs,
            "pending_jobs": batch.pending_jobs,
            "created_at": batch.created_at.isoformat(),
            "started_at": batch.started_at.isoformat() if batch.started_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
        }

    def _job_to_dict_detail(self, job: BatchJobModel) -> dict:
        """Return job dict with team + match sub-objects for frontend display."""
        team_data = {"id": str(job.team_id), "name": "", "code": ""}
        match_data = {"id": str(job.match_id), "home_team_name": "", "away_team_name": ""}
        try:
            team = self.db.query(TeamModel).filter(TeamModel.id == job.team_id).first()
            if team:
                team_data = {"id": str(team.id), "name": team.name, "code": team.team_id or ""}
        except Exception:
            pass
        try:
            match = self.db.query(MatchModel).filter(MatchModel.id == job.match_id).first()
            if match:
                match_data = {
                    "id": str(match.id),
                    "home_team_name": match.home_team_name,
                    "away_team_name": match.away_team_name,
                }
        except Exception:
            pass
        return {
            "id": str(job.id),
            "batch_id": str(job.batch_id),
            "team": team_data,
            "match": match_data,
            "status": job.status,
            "error_message": job.error_message,
            "prediction_id": str(job.prediction_id) if job.prediction_id else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
