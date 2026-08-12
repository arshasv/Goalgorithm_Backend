import csv
import io
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, List
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.enums import MatchStatus, ExternalSyncStatus, Winner
from app.models.match import MatchModel
from app.models.actual_result import ActualResultModel
from app.models.user import UserModel
from app.schemas.match_schema import MatchCreate, MatchUpdate
from app.repositories.match_repository import MatchRepository, ActualResultRepository
from app.services.football_api_service import FootballAPIService, FootballAPIError
from app.services.scoring_service import ScoringService

def _serialize(m: MatchModel) -> dict:
    ext_sync = m.external_sync_status
    if hasattr(ext_sync, "value"):
        ext_sync = ext_sync.value
    
    # Check for actual results to compute dynamic status and include scores
    home_score = None
    away_score = None
    if hasattr(m, '_actual_home_goals') and m._actual_home_goals is not None:
        home_score = m._actual_home_goals
    if hasattr(m, '_actual_away_goals') and m._actual_away_goals is not None:
        away_score = m._actual_away_goals

    if home_score is not None and away_score is not None:
        status_val = MatchStatus.COMPLETED
    else:
        now = datetime.now(timezone.utc)
        if m.scheduled_at < now:
            status_val = MatchStatus.AWAITING_RESULT
        else:
            status_val = MatchStatus.SCHEDULED

    return {
        "id": str(m.id),
        "match_number": m.match_number,
        "home_team_name": m.home_team_name,
        "away_team_name": m.away_team_name,
        "scheduled_at": m.scheduled_at.isoformat(),
        "freeze_deadline": m.freeze_deadline.isoformat(),
        "round": m.round,
        "status": status_val.value if hasattr(status_val, "value") else str(status_val),
        "created_at": m.created_at.isoformat(),
        "external_api_id": m.external_api_id,
        "competition_name": m.competition_name,
        "external_sync_status": ext_sync,
        "home_score": home_score,
        "away_score": away_score,
    }

def map_api_status_to_match_status(short_status: str) -> MatchStatus:
    if short_status in ("FT", "AET", "PEN"):
        return MatchStatus.COMPLETED
    return MatchStatus.SCHEDULED


class MatchService:
    def __init__(
        self,
        match_repo: MatchRepository,
        actual_repo: ActualResultRepository,
        scoring_service: ScoringService,
    ) -> None:
        self.match_repo = match_repo
        self.actual_repo = actual_repo
        self.scoring_service = scoring_service

    def list_matches(self) -> list[dict]:
        matches = self.match_repo.get_all_ordered()
        return [_serialize(m) for m in matches]

    def create_match(self, payload: MatchCreate) -> dict:
        # Validate match_number uniqueness
        existing = self.match_repo.get_by_match_number(payload.match_number)
        if existing:
            raise HTTPException(status_code=400, detail="Match number already exists")
        freeze = payload.freeze_deadline or (payload.scheduled_at - timedelta(hours=1))
        match = self.match_repo.create(
            match_number=payload.match_number,
            home_team_name=payload.home_team_name,
            away_team_name=payload.away_team_name,
            scheduled_at=payload.scheduled_at,
            freeze_deadline=freeze,
            round=payload.round,
            status=MatchStatus.SCHEDULED,
        )
        return _serialize(match)

    def update_match(self, match_id: uuid.UUID, payload: MatchUpdate) -> dict:
        match = self.match_repo.get(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        updates = {}
        if payload.home_team_name is not None:
            updates["home_team_name"] = payload.home_team_name.strip()
        if payload.away_team_name is not None:
            updates["away_team_name"] = payload.away_team_name.strip()
        if payload.scheduled_at is not None:
            updates["scheduled_at"] = payload.scheduled_at
        if payload.freeze_deadline is not None:
            updates["freeze_deadline"] = payload.freeze_deadline
        if payload.round is not None:
            updates["round"] = payload.round

        match = self.match_repo.update(match, **updates)
        return _serialize(match)

    def delete_match(self, match_id: uuid.UUID) -> None:
        match = self.match_repo.get(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        db = self.match_repo.db
        from app.models.prediction import PredictionModel, PlayerPredictionModel
        from app.models.score import ScoreModel
        from app.models.actual_result import ActualResultModel, PlayerActualModel
        from app.model_execution.models.model_upload import ModelUploadModel
        from app.model_execution.models.model_execution import ModelExecutionModel

        sync = 'fetch'

        # Cascade delete related data — match_id is UUID, columns are Uuid(as_uuid=True)
        db.query(ScoreModel).filter(ScoreModel.match_id == match_id).delete(synchronize_session=sync)

        # Model uploads and their execution children (delete BEFORE predictions/actuals)
        uploads = db.query(ModelUploadModel.id).filter(ModelUploadModel.match_id == match_id).all()
        if uploads:
            upload_ids = [r[0] for r in uploads]
            db.query(ModelExecutionModel).filter(
                ModelExecutionModel.model_upload_id.in_(upload_ids)
            ).delete(synchronize_session=sync)
            db.query(ModelUploadModel).filter(
                ModelUploadModel.match_id == match_id
            ).delete(synchronize_session=sync)

        # Predictions and their children
        preds = db.query(PredictionModel.id).filter(PredictionModel.match_id == match_id).all()
        if preds:
            pred_ids = [r[0] for r in preds]
            db.query(ModelExecutionModel).filter(
                ModelExecutionModel.prediction_id.in_(pred_ids)
            ).delete(synchronize_session=sync)
            db.query(PlayerPredictionModel).filter(
                PlayerPredictionModel.prediction_id.in_(pred_ids)
            ).delete(synchronize_session=sync)
            db.query(PredictionModel).filter(
                PredictionModel.id.in_(pred_ids)
            ).delete(synchronize_session=sync)

        # Actual results and their children
        results = db.query(ActualResultModel.id).filter(ActualResultModel.match_id == match_id).all()
        if results:
            res_ids = [r[0] for r in results]
            db.query(PlayerActualModel).filter(
                PlayerActualModel.actual_result_id.in_(res_ids)
            ).delete(synchronize_session=sync)
            db.query(ActualResultModel).filter(
                ActualResultModel.id.in_(res_ids)
            ).delete(synchronize_session=sync)

        # Mark match for deletion
        db.delete(match)
        db.flush()
        db.expire_all()
        db.commit()

    def upload_match_csv(self, content: str) -> dict:
        reader = csv.DictReader(io.StringIO(content))
        REQUIRED = {"match_number", "home_team", "away_team", "kickoff_date"}
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV has no headers")

        normalised = [f.strip().lower() for f in reader.fieldnames]
        missing = REQUIRED - set(normalised)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"CSV missing required columns: {', '.join(sorted(missing))}",
            )

        created: List[dict] = []
        errors: List[str] = []

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

                if self.match_repo.get_by_match_number(match_number):
                    errors.append(f"Row {i}: Match number {match_number} already exists")
                    continue

                freeze = kickoff - timedelta(hours=1)
                match = self.match_repo.create(
                    match_number=match_number,
                    home_team_name=home,
                    away_team_name=away,
                    scheduled_at=kickoff,
                    freeze_deadline=freeze,
                    round=round_val,
                    status=MatchStatus.SCHEDULED,
                )
                created.append(_serialize(match))

            except Exception as exc:
                errors.append(f"Row {i}: {exc}")

        return {
            "created": len(created),
            "errors": errors,
            "matches": created,
        }

    async def get_fixtures(self, target_date: date) -> list[dict[str, Any]]:
        service = FootballAPIService()
        try:
            return await service.fetch_fixtures_by_date(target_date)
        except FootballAPIError as e:
            raise HTTPException(status_code=502, detail=str(e))

    async def import_fixtures(self, target_date: date) -> dict:
        service = FootballAPIService()
        try:
            fixtures = await service.fetch_fixtures_by_date(target_date)
        except FootballAPIError as e:
            raise HTTPException(status_code=502, detail=str(e))

        created_count = 0
        updated_count = 0

        max_match_num = self.match_repo.get_max_match_number()

        for f in fixtures:
            ext_api_id = str(f["external_api_id"])
            scheduled_at = datetime.fromisoformat(f["scheduled_at"])
            existing_match = self.match_repo.get_by_external_api_id(ext_api_id)

            if existing_match:
                self.match_repo.update(
                    existing_match,
                    home_team_name=f["home_team_name"],
                    away_team_name=f["away_team_name"],
                    scheduled_at=scheduled_at,
                    competition_name=f["competition_name"],
                    status=map_api_status_to_match_status(f["status"]),
                )
                updated_count += 1
            else:
                max_match_num += 1
                self.match_repo.create(
                    match_number=max_match_num,
                    home_team_name=f["home_team_name"],
                    away_team_name=f["away_team_name"],
                    scheduled_at=scheduled_at,
                    freeze_deadline=scheduled_at,
                    status=map_api_status_to_match_status(f["status"]),
                    external_api_id=ext_api_id,
                    competition_name=f["competition_name"],
                    external_sync_status=ExternalSyncStatus.PENDING,
                )
                created_count += 1

        return {
            "created_count": created_count,
            "updated_count": updated_count,
            "matches": fixtures,
        }

    async def sync_results(self, current_organizer: UserModel) -> dict:
        from app.services.scoring_service import ScoringService

        matches_to_sync = self.match_repo.get_matches_for_sync([
            MatchStatus.COMPLETED,
            MatchStatus.SCORED,
            MatchStatus.RESULT_ENTERED
        ])

        if not matches_to_sync:
            return {"completed_matches": 0, "skipped_matches": 0, "results_created": 0}

        api_id_to_match = {m.external_api_id: m for m in matches_to_sync}

        service = FootballAPIService()
        try:
            results = await service.fetch_fixtures_by_ids(list(api_id_to_match.keys()))
        except FootballAPIError as e:
            raise HTTPException(status_code=502, detail=str(e))

        completed_matches = 0
        skipped_matches = 0
        results_created = 0

        for r in results:
            api_id = r["external_api_id"]
            status = r["status"]

            if status not in ("FT", "AET", "PEN"):
                skipped_matches += 1
                continue

            completed_matches += 1
            match_record = api_id_to_match[api_id]

            existing_result = self.actual_repo.get_by_match_id(str(match_record.id))
            if existing_result:
                continue

            self.actual_repo.create(
                match_id=str(match_record.id),
                actual_winner=Winner(r["winner"]),
                actual_home_goals=r["home_goals"] or 0,
                actual_away_goals=r["away_goals"] or 0,
                goal_scorers={"home": [], "away": []},
                result_source="API",
                last_synced_at=datetime.utcnow(),
            )

            self.match_repo.update(
                match_record,
                status=MatchStatus.COMPLETED,
                external_sync_status=ExternalSyncStatus.SYNCED,
            )
            results_created += 1

        scoring_service = self.scoring_service
        for r in results:
            api_id = r["external_api_id"]
            status = r["status"]
            if status in ("FT", "AET", "PEN"):
                match_record = api_id_to_match[api_id]
                try:
                    scoring_service.calculate_all_scores_for_match(str(match_record.id))
                except Exception as e:
                    print(f"Error calculating scores for match {match_record.id}: {e}")

        return {
            "completed_matches": completed_matches,
            "skipped_matches": skipped_matches,
            "results_created": results_created,
        }
