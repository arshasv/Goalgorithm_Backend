from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_organizer
from app.schemas.model_evaluation_schema import (
    ModelEvaluationCreate,
    ModelEvaluationResponse,
    ModelEvaluationAnalyticsResponse,
)
from app.services.model_evaluation_service import ModelEvaluationService

router = APIRouter(prefix="/api/v1/model-evaluations", tags=["Model Evaluations"])


@router.get("/models")
def get_submitted_models(
    db: Session = Depends(get_db),
    _=Depends(get_current_organizer),
) -> list[dict]:
    """
    Get all submitted models across teams.
    Returns: team, model name, version, upload date, status, active flag
    """
    service = ModelEvaluationService(db)
    return service.get_submitted_models()


@router.post("", response_model=ModelEvaluationResponse)
def save_model_evaluation(
    data: ModelEvaluationCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_organizer),
):
    """
    Save model evaluation manually.
    Automatically calculates strength/weakness based on percentage values.
    """
    service = ModelEvaluationService(db)
    return service.save_evaluation(data)


from fastapi import HTTPException
from app.models.leaderboard_visibility import LeaderboardVisibilityModel
from app.api.deps import get_current_user

def _check_model_eval_visibility(
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role == "TEAM_LEADER":
        settings = db.query(LeaderboardVisibilityModel).first()
        if not settings or not settings.analytics_visibility_enabled or not settings.show_model_analytics:
            raise HTTPException(status_code=403, detail="Model analytics are disabled")
    return user


@router.get("/analytics", response_model=ModelEvaluationAnalyticsResponse)
def get_model_analytics(
    db: Session = Depends(get_db),
    _=Depends(_check_model_eval_visibility),
):
    """
    Get analytics data including team rankings, model scores, accuracy comparison, category breakdown, version history.
    """
    service = ModelEvaluationService(db)
    return service.get_analytics()
