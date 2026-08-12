from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer
from app.database.session import get_db
from app.models.leaderboard_visibility import LeaderboardVisibilityModel
from app.models.user import UserModel
from app.schemas.leaderboard_visibility_schema import (
    LeaderboardVisibilityResponse,
    LeaderboardVisibilityUpdate,
)

router = APIRouter(prefix="/admin/leaderboard", tags=["admin-leaderboard"])


def get_or_create_settings(db: Session) -> LeaderboardVisibilityModel:
    settings = db.query(LeaderboardVisibilityModel).first()
    if not settings:
        settings = LeaderboardVisibilityModel()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/settings", response_model=LeaderboardVisibilityResponse)
def get_leaderboard_settings(
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    return get_or_create_settings(db)


@router.put("/settings", response_model=LeaderboardVisibilityResponse)
def update_leaderboard_settings(
    update_data: LeaderboardVisibilityUpdate,
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    settings = get_or_create_settings(db)
    update_dict = update_data.model_dump(exclude_none=True)
    for key, value in update_dict.items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings
