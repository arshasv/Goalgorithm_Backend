import logging
import secrets
import re
import string

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer
from app.auth.auth_service import hash_password
from app.database.session import get_db
from app.email.service import EmailService
from app.models.enums import UserRole
from app.models.team import TeamModel
from app.models.user import UserModel
from app.utils.email_validator import validate_email_domain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=255)
    team_name: str = Field(..., min_length=1, max_length=255)
    team_leader_name: str = Field(..., min_length=1, max_length=255)


class AdminCreateUserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    team_id: str | None = None
    team_name: str | None = None


def _generate_temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.post("/create-user", status_code=201, response_model=AdminCreateUserResponse)
def admin_create_user(
    body: AdminCreateUserRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    email_err = validate_email_domain(body.email)
    if email_err:
        raise HTTPException(status_code=422, detail=email_err)

    if db.query(UserModel).filter(UserModel.username == body.username).first():
        raise HTTPException(status_code=409, detail="Username already taken")

    if db.query(UserModel).filter(UserModel.email == body.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Generate temporary password — kept in memory only, never stored
    temp_password = _generate_temporary_password()

    user = UserModel(
        username=body.username,
        email=body.email.lower(),
        password_hash=hash_password(temp_password),
        role=UserRole.TEAM_LEADER,
        is_active=True,
    )
    db.add(user)
    db.flush()

    team_val = body.team_name.strip().upper()
    team_letter = re.sub(r"^TEAM[\s_]*", "", team_val)
    if team_letter not in ["A", "B", "C", "D", "E"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid team. Only Teams A, B, C, D, E are allowed.",
        )

    existing_team = (
        db.query(TeamModel).filter(TeamModel.team_id == team_letter).first()
    )
    if existing_team:
        if existing_team.user_id is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Team '{team_letter}' already has a registered team leader.",
            )
        existing_team.user_id = user.id
        existing_team.team_leader_name = body.team_leader_name
        team = existing_team
    else:
        team = TeamModel(
            team_id=team_letter,
            name=f"Team {team_letter}",
            code=team_letter,
            team_leader_name=body.team_leader_name,
            user_id=user.id,
        )
        db.add(team)

    db.commit()
    db.refresh(user)
    db.refresh(team)

    # Send welcome email in the background
    # The plain temp_password exists only in this variable until the task runs
    background_tasks.add_task(
        EmailService().send_welcome_email,
        to_email=user.email,
        name=body.team_leader_name,
        username=user.username,
        temporary_password=temp_password,
    )

    return AdminCreateUserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        team_id=str(team.id),
        team_name=team.name,
    )
