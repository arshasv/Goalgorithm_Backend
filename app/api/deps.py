import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth_bearer import security
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.team import TeamModel
from app.models.user import UserModel


def get_current_user(
    payload: dict = Depends(security),
    db: Session = Depends(get_db),
) -> UserModel:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    try:
        user = db.query(UserModel).filter(UserModel.id == uuid.UUID(user_id)).first()
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid user ID in token")
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_organizer(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    if current_user.role != UserRole.ORGANIZER:
        raise HTTPException(status_code=403, detail="Organizer access required")
    return current_user


def get_current_team_leader(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    if current_user.role != UserRole.TEAM_LEADER:
        raise HTTPException(status_code=403, detail="Team leader access required")
    return current_user


def get_current_team(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamModel:
    team = db.query(TeamModel).filter(TeamModel.user_id == current_user.id).first()
    if not team:
        from app.api.auth_routes import _ensure_team_link
        team = _ensure_team_link(current_user, db)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found for current user")
    return team
