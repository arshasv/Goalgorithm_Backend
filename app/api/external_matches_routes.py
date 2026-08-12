from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_organizer
from app.database.session import get_db
from app.services.football_api_service import FootballAPIError, FootballAPIService
from app.models.match import MatchModel
from app.models.enums import MatchStatus, ExternalSyncStatus

router = APIRouter(tags=["external-matches"])

class ImportRequest(BaseModel):
    target_date: date

def map_api_status_to_match_status(short_status: str) -> MatchStatus:
    if short_status in ("FT", "AET", "PEN"):
        return MatchStatus.COMPLETED
    return MatchStatus.SCHEDULED

@router.get("/external-matches/fixtures")
async def get_fixtures(
    target_date: date,
    _organizer: object = Depends(get_current_organizer),
) -> list[dict[str, Any]]:
    service = FootballAPIService()
    try:
        fixtures = await service.fetch_fixtures_by_date(target_date)
        return fixtures
    except FootballAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.post("/external-matches/import")
async def import_fixtures(
    request: ImportRequest,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    service = FootballAPIService()
    try:
        fixtures = await service.fetch_fixtures_by_date(request.target_date)
    except FootballAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
        
    created_count = 0
    updated_count = 0
    
    # Get current max match_number
    max_match_num = db.query(func.max(MatchModel.match_number)).scalar() or 0
    
    for f in fixtures:
        ext_api_id = str(f["external_api_id"])
        
        # Parse datetime
        scheduled_at = datetime.fromisoformat(f["scheduled_at"])
        
        # Check if match exists
        existing_match = db.query(MatchModel).filter(MatchModel.external_api_id == ext_api_id).first()
        
        if existing_match:
            # Update existing
            existing_match.home_team_name = f["home_team_name"]
            existing_match.away_team_name = f["away_team_name"]
            existing_match.scheduled_at = scheduled_at
            existing_match.competition_name = f["competition_name"]
            existing_match.status = map_api_status_to_match_status(f["status"])
            updated_count += 1
        else:
            # Insert new
            max_match_num += 1
            new_match = MatchModel(
                match_number=max_match_num,
                home_team_name=f["home_team_name"],
                away_team_name=f["away_team_name"],
                scheduled_at=scheduled_at,
                freeze_deadline=scheduled_at,
                status=map_api_status_to_match_status(f["status"]),
                external_api_id=ext_api_id,
                competition_name=f["competition_name"],
                external_sync_status=ExternalSyncStatus.PENDING
            )
            db.add(new_match)
            created_count += 1
            
    db.commit()
    
    return {
        "created_count": created_count,
        "updated_count": updated_count,
        "matches": fixtures
    }

@router.post("/external-matches/sync-results")
async def sync_results(
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    from app.api.scoring_routes import calculate_all_scores_for_match
    from app.models.actual_result import ActualResultModel
    from app.models.enums import Winner
    
    # 1. Find all imported matches that are not COMPLETED/SCORED/RESULT_ENTERED
    matches_to_check = db.query(MatchModel).filter(
        MatchModel.external_api_id.isnot(None),
        MatchModel.status.notin_([MatchStatus.COMPLETED, MatchStatus.SCORED, MatchStatus.RESULT_ENTERED])
    ).all()
    
    if not matches_to_check:
        return {"completed_matches": 0, "skipped_matches": 0, "results_created": 0}
        
    api_id_to_match = {m.external_api_id: m for m in matches_to_check}
    
    # 2. Fetch fixtures from API
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
        
        # Check if actual result already exists
        existing_result = db.query(ActualResultModel).filter(ActualResultModel.match_id == match_record.id).first()
        if existing_result:
            continue
            
        # Create ActualResultModel
        actual_result = ActualResultModel(
            match_id=match_record.id,
            actual_winner=Winner(r["winner"]),
            actual_home_goals=r["home_goals"] or 0,
            actual_away_goals=r["away_goals"] or 0,
            goal_scorers={"home": [], "away": []},
            result_source="API",
            last_synced_at=datetime.utcnow()
        )
        db.add(actual_result)
        
        # Update MatchModel
        match_record.status = MatchStatus.COMPLETED
        match_record.external_sync_status = ExternalSyncStatus.SYNCED
        results_created += 1
        
    db.commit()
    
    # Trigger scoring engine for each match that just got a result
    for r in results:
        api_id = r["external_api_id"]
        status = r["status"]
        if status in ("FT", "AET", "PEN"):
            match_record = api_id_to_match[api_id]
            try:
                calculate_all_scores_for_match(str(match_record.id), db, _organizer)
            except Exception as e:
                # Log error but continue
                print(f"Error calculating scores for match {match_record.id}: {e}")
                
    return {
        "completed_matches": completed_matches,
        "skipped_matches": skipped_matches,
        "results_created": results_created
    }
