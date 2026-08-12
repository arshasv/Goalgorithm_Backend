import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.leaderboard_visibility import LeaderboardVisibilityModel
from app.models.user import UserModel
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])


def _check_overview_visibility(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserModel:
    if user.role == "TEAM_LEADER":
        settings = db.query(LeaderboardVisibilityModel).first()
        if not settings or not settings.analytics_visibility_enabled or not (settings.show_overall_comparison or settings.show_leaderboard_analytics):
            raise HTTPException(status_code=403, detail="Overview analytics are disabled")
    return user

def _check_model_visibility(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserModel:
    if user.role == "TEAM_LEADER":
        settings = db.query(LeaderboardVisibilityModel).first()
        if not settings or not settings.analytics_visibility_enabled or not settings.show_model_analytics:
            raise HTTPException(status_code=403, detail="Model analytics are disabled")
    return user

def _check_presentation_visibility(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserModel:
    if user.role == "TEAM_LEADER":
        settings = db.query(LeaderboardVisibilityModel).first()
        if not settings or not settings.analytics_visibility_enabled or not settings.show_presentation_analytics:
            raise HTTPException(status_code=403, detail="Presentation analytics are disabled")
    return user

def _check_judge_visibility(
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserModel:
    if user.role == "TEAM_LEADER":
        settings = db.query(LeaderboardVisibilityModel).first()
        if not settings or not settings.analytics_visibility_enabled or not settings.show_judge_analytics:
            raise HTTPException(status_code=403, detail="Judge analytics are disabled")
    return user


# ---------------------------------------------------------------------------
# GET /analytics/overview
# ---------------------------------------------------------------------------

@router.get("/analytics/overview")
def analytics_overview(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(_check_overview_visibility),
):
    service = AnalyticsService(db)
    return service.get_overview()


# ---------------------------------------------------------------------------
# GET /analytics/models
# ---------------------------------------------------------------------------

@router.get("/analytics/models")
def analytics_models(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(_check_model_visibility),
):
    service = AnalyticsService(db)
    return service.get_models_analytics()


# ---------------------------------------------------------------------------
# GET /analytics/presentation
# ---------------------------------------------------------------------------

@router.get("/analytics/presentation")
def analytics_presentation(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(_check_presentation_visibility),
):
    service = AnalyticsService(db)
    return service.get_presentation_analytics()


# ---------------------------------------------------------------------------
# GET /analytics/judges
# ---------------------------------------------------------------------------

@router.get("/analytics/judges")
def analytics_judges(
    db: Session = Depends(get_db),
    _user: UserModel = Depends(_check_judge_visibility),
):
    service = AnalyticsService(db)
    return service.get_judge_analytics()


# ---------------------------------------------------------------------------
# GET /analytics/team/{team_id}
# ---------------------------------------------------------------------------

@router.get("/analytics/team/{team_id}")
def analytics_team(
    team_id: str,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    service = AnalyticsService(db)
    result = service.get_team_analytics(team_id)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found")
    return result
