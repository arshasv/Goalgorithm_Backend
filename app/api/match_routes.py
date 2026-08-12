"""Match management routes — organizer CRUD + CSV/Excel upload."""
from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_current_user
from app.database.session import get_db
from app.models.enums import MatchStatus, UserRole
from app.models.match import MatchModel
from app.models.user import UserModel
from app.schemas.match_schema import MatchCreate, MatchUpdate, MatchResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/matches", tags=["matches"])


def _serialize(m: MatchModel, act=None) -> dict:
    ext_sync = m.external_sync_status
    if hasattr(ext_sync, "value"):
        ext_sync = ext_sync.value

    # Dynamically compute status — RESULT ALWAYS OVERRIDES DATE
    home_score = act.actual_home_goals if act else None
    away_score = act.actual_away_goals if act else None

    if home_score is not None and away_score is not None:
        status = MatchStatus.COMPLETED
    else:
        now = datetime.now(timezone.utc)
        if m.scheduled_at < now:
            status = MatchStatus.AWAITING_RESULT
        else:
            status = MatchStatus.SCHEDULED

    return {
        "id": str(m.id),
        "match_number": m.match_number,
        "home_team_name": m.home_team_name,
        "away_team_name": m.away_team_name,
        "scheduled_at": m.scheduled_at.isoformat(),
        "freeze_deadline": m.freeze_deadline.isoformat(),
        "round": m.round,
        "status": status.value if hasattr(status, "value") else str(status),
        "created_at": m.created_at.isoformat(),
        "external_api_id": m.external_api_id,
        "competition_name": m.competition_name,
        "external_sync_status": ext_sync,
        "home_score": home_score,
        "away_score": away_score,
        "actual_home_goals": home_score,
        "actual_away_goals": away_score,
    }


# ── List all matches (any authenticated user) ──────────────────────────────

@router.get("")
def list_matches(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    from app.models.actual_result import ActualResultModel
    matches = db.query(MatchModel).order_by(MatchModel.match_number).all()
    actuals = db.query(ActualResultModel).all()
    actuals_map = {a.match_id: a for a in actuals}
    
    result = []
    for m in matches:
        act = actuals_map.get(m.id)
        m_dict = _serialize(m, act)
        result.append(m_dict)
    return result


# ── Create a single match (organizer only) ─────────────────────────────────

@router.post("", status_code=201)
def create_match(
    payload: MatchCreate,
    db: Session = Depends(get_db),
    _organizer: UserModel = Depends(get_current_organizer),
):
    logger.warning(f"--- CREATE_MATCH called for match_number={payload.match_number} ---")
    # check if match_number already exists
    existing_match = db.query(MatchModel).filter(MatchModel.match_number == payload.match_number).first()
    logger.warning(f"--- existing_match result: {existing_match is not None} ---")
    if existing_match:
        logger.warning(f"=== DUPLICATE DETECTED: match_number {payload.match_number} ===")
        raise HTTPException(status_code=400, detail="Match number already exists")

    # auto-compute freeze_deadline if not supplied (1 hour before kickoff)
    freeze = payload.freeze_deadline or (payload.scheduled_at - timedelta(hours=1))

    match = MatchModel(
        match_number=payload.match_number,
        home_team_name=payload.home_team_name,
        away_team_name=payload.away_team_name,
        scheduled_at=payload.scheduled_at,
        freeze_deadline=freeze,
        round=payload.round,
        status=MatchStatus.SCHEDULED,
    )
    logger.warning(f"--- Adding match with num={payload.match_number} to session ---")
    db.add(match)
    try:
        logger.warning("--- Attempting db.commit() ---")
        db.commit()
        logger.warning("--- db.commit() SUCCEEDED ---")
    except Exception as e:
        db.rollback()
        logger.error(f"=== COMMIT FAILED: {e} ===")
        raise HTTPException(status_code=400, detail=f"Match number {payload.match_number} already exists")
    db.refresh(match)
    logger.warning("--- Returning serialized match ---")
    return _serialize(match)


# ── Update a match (organizer only) ───────────────────────────────────────

@router.put("/{match_id}")
def update_match(
    match_id: uuid.UUID,
    payload: MatchUpdate,
    db: Session = Depends(get_db),
    _organizer: UserModel = Depends(get_current_organizer),
):
    match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    if payload.home_team_name is not None:
        match.home_team_name = payload.home_team_name.strip()
    if payload.away_team_name is not None:
        match.away_team_name = payload.away_team_name.strip()
    if payload.scheduled_at is not None:
        match.scheduled_at = payload.scheduled_at
    if payload.freeze_deadline is not None:
        match.freeze_deadline = payload.freeze_deadline
    if payload.round is not None:
        match.round = payload.round

    db.commit()
    db.refresh(match)
    return _serialize(match)


# ── Delete a match (organizer only) ───────────────────────────────────────

@router.delete("/{match_id}", status_code=204)
def delete_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    _organizer: UserModel = Depends(get_current_organizer),
):
    match = db.query(MatchModel).filter(MatchModel.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    from app.models.score import ScoreModel
    from app.models.actual_result import ActualResultModel, PlayerActualModel
    from app.models.prediction import PredictionModel, PlayerPredictionModel
    from app.model_execution.models.model_upload import ModelUploadModel
    from app.model_execution.models.model_execution import ModelExecutionModel
    from app.services.scoring_service import ScoringService

    logger.warning(f"Deleting match {match_id} (match_number={match.match_number})")

    try:
        # 1. Delete scores
        n = db.query(ScoreModel).filter(ScoreModel.match_id == match_id).delete(synchronize_session='fetch')
        if n:
            logger.warning(f"  Deleted {n} score(s)")

        # 2. Delete player actuals (children of actual_results)
        actual_ids = [
            r[0] for r in
            db.query(ActualResultModel.id).filter(ActualResultModel.match_id == match_id).all()
        ]
        if actual_ids:
            n = db.query(PlayerActualModel).filter(
                PlayerActualModel.actual_result_id.in_(actual_ids)
            ).delete(synchronize_session='fetch')
            logger.warning(f"  Deleted {n} player actual(s)")

        # 3. Delete player predictions & model executions tied to predictions
        pred_ids = [
            r[0] for r in
            db.query(PredictionModel.id).filter(PredictionModel.match_id == match_id).all()
        ]
        if pred_ids:
            n = db.query(PlayerPredictionModel).filter(
                PlayerPredictionModel.prediction_id.in_(pred_ids)
            ).delete(synchronize_session='fetch')
            logger.warning(f"  Deleted {n} player prediction(s)")

            n = db.query(ModelExecutionModel).filter(
                ModelExecutionModel.prediction_id.in_(pred_ids)
            ).delete(synchronize_session='fetch')
            logger.warning(f"  Deleted {n} model execution(s) (by prediction_id)")

        # 4. Delete model executions tied to model uploads & model uploads
        upload_ids = [
            r[0] for r in
            db.query(ModelUploadModel.id).filter(ModelUploadModel.match_id == match_id).all()
        ]
        if upload_ids:
            n = db.query(ModelExecutionModel).filter(
                ModelExecutionModel.model_upload_id.in_(upload_ids)
            ).delete(synchronize_session='fetch')
            if n:
                logger.warning(f"  Deleted {n} model execution(s) (by model_upload_id)")

            n = db.query(ModelUploadModel).filter(
                ModelUploadModel.match_id == match_id
            ).delete(synchronize_session='fetch')
            logger.warning(f"  Deleted {n} model upload(s)")

        # 5. Delete actual results and predictions (parents of children above)
        n = db.query(ActualResultModel).filter(
            ActualResultModel.match_id == match_id
        ).delete(synchronize_session='fetch')
        if n:
            logger.warning(f"  Deleted {n} actual result(s)")

        n = db.query(PredictionModel).filter(
            PredictionModel.match_id == match_id
        ).delete(synchronize_session='fetch')
        if n:
            logger.warning(f"  Deleted {n} prediction(s)")

        # 6. Delete the match itself
        db.delete(match)
        db.flush()
        db.expire_all()
        db.commit()
        logger.warning(f"Match {match_id} deleted successfully")

        try:
            service = ScoringService(db)
            service.compute_and_save_leaderboard(None)
        except Exception as e:
            logger.error(f"Failed to recalculate leaderboard after deleting match {match_id}: {e}")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete match {match_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while deleting the match")


# ── CSV upload (organizer only) ────────────────────────────────────────────
# Expected columns: match_number, home_team, away_team, kickoff_date, round
# Example row:  1,Argentina,Brazil,2026-06-17T18:00:00,Group Stage

@router.post("/upload-csv", status_code=201)
def upload_match_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _organizer: UserModel = Depends(get_current_organizer),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ("csv",):
        raise HTTPException(status_code=400, detail="Only .csv files are supported for upload")

    content = file.file.read().decode("utf-8-sig")  # strip BOM if present
    reader = csv.DictReader(io.StringIO(content))

    # normalise header names
    REQUIRED = {"match_number", "home_team", "away_team", "kickoff_date"}
    if reader.fieldnames:
        normalised = [f.strip().lower() for f in reader.fieldnames]
    else:
        raise HTTPException(status_code=400, detail="CSV has no headers")

    missing = REQUIRED - set(normalised)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(sorted(missing))}",
        )

    created: List[dict] = []
    errors: List[str] = []
    seen_match_numbers = set()

    for i, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items()}
        try:
            match_number = int(row["match_number"])
            home = row["home_team"]
            away = row["away_team"]
            kickoff_str = row["kickoff_date"]
            round_val = row.get("round", "").strip() or None

            if not home or not away:
                errors.append(f"Row {i}: home/away team name is empty")
                continue

            if match_number in seen_match_numbers:
                errors.append(f"Row {i}: Match number {match_number} is duplicated in the CSV")
                continue
            
            existing_match = db.query(MatchModel).filter(MatchModel.match_number == match_number).first()
            if existing_match:
                errors.append(f"Row {i}: Match number {match_number} already exists")
                continue
            
            seen_match_numbers.add(match_number)

            # parse kickoff — try ISO first, then date-only
            kickoff: datetime
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
                try:
                    kickoff = datetime.strptime(kickoff_str, fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue
            else:
                errors.append(f"Row {i}: cannot parse kickoff_date '{kickoff_str}'")
                continue

            freeze = kickoff - timedelta(hours=1)
            match = MatchModel(
                match_number=match_number,
                home_team_name=home,
                away_team_name=away,
                scheduled_at=kickoff,
                freeze_deadline=freeze,
                round=round_val,
                status=MatchStatus.SCHEDULED,
            )
            db.add(match)
            db.flush()
            created.append(_serialize(match))

        except Exception as exc:
            errors.append(f"Row {i}: {exc}")

    db.commit()
    return {
        "created": len(created),
        "errors": errors,
        "matches": created,
    }
