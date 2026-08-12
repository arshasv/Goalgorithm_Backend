import re
import string
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.models.team import TeamModel
from app.models.user import UserModel
from app.models.password_reset_otp import PasswordResetOtpModel
from app.repositories.user_repository import UserRepository, PasswordResetOtpRepository
from app.repositories.team_repository import TeamRepository
from app.utils.email_validator import validate_email_domain
from app.auth.auth_utils import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.email.service import EmailService
from app.schemas.auth_schema import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UserResponse,
    UserInfo,
)
from app.schemas.admin_auth_schema import (
    AdminCreateUserRequest,
    AdminCreateUserResponse,
)

def _extract_team_code(email: str, team_name: str | None = None) -> str | None:
    local_part = email.lower().split("@")[0].strip()
    match = re.match(r'^team(\w+)$', local_part)
    if match:
        return match.group(1).upper()
    if team_name:
        val = team_name.strip().upper()
        return re.sub(r'^TEAM[\s_]*', '', val)
    return None

def _generate_temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        otp_repo: PasswordResetOtpRepository,
    ) -> None:
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.otp_repo = otp_repo

    def _ensure_team_link(self, user: UserModel) -> TeamModel | None:
        if str(user.role).upper() != UserRole.TEAM_LEADER.value:
            return None
        user_teams = self.team_repo.get_by_user_id(user.id)
        team = user_teams[0] if user_teams else None
        if team:
            return team
        team_code = _extract_team_code(user.email, None)
        if not team_code:
            return None
        team = self.team_repo.get_by_code(team_code)
        if team and team.user_id is None:
            team.user_id = user.id
            self.team_repo.save(team)
            return team
        return None

    def register(self, body: RegisterRequest) -> RegisterResponse:
        email_err = validate_email_domain(body.email)
        if email_err:
            raise HTTPException(status_code=422, detail=email_err)

        if self.user_repo.get_by_username(body.username):
            raise HTTPException(status_code=409, detail="Username already taken")

        if self.user_repo.get_by_email(body.email):
            raise HTTPException(status_code=409, detail="Email already registered")

        user = UserModel(
            username=body.username,
            email=body.email.lower(),
            password_hash=hash_password(body.password),
            role=UserRole.TEAM_LEADER,
            is_active=True,
        )
        user = self.user_repo.create(**{
            "username": user.username,
            "email": user.email,
            "password_hash": user.password_hash,
            "role": user.role,
            "is_active": user.is_active,
        })

        team_code = _extract_team_code(body.email, body.team_name)
        if not team_code:
            raise HTTPException(
                status_code=400,
                detail="Could not determine team code. Use an email like teamX@domain.com or provide team_name."
            )

        team = self.team_repo.get_by_code(team_code)
        if team:
            if team.user_id is not None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Team '{team_code}' already has a registered team leader."
                )
            team.user_id = user.id
            team.team_leader_name = body.team_leader_name
            self.team_repo.save(team)
        else:
            team = TeamModel(
                team_id=team_code,
                name=f"Team {team_code}",
                code=team_code,
                team_leader_name=body.team_leader_name,
                user_id=user.id,
            )
            team = self.team_repo.create(team)

        token = create_access_token(data={"sub": str(user.id), "role": user.role.value if hasattr(user.role, 'value') else str(user.role)})
        return RegisterResponse(
            access_token=token,
            token_type="bearer",
            user=UserInfo(
                id=str(user.id),
                username=user.username,
                email=user.email,
                role=user.role,
                team_id=str(team.id),
                team_name=team.name,
            ),
        )

    def login(self, body: LoginRequest) -> LoginResponse:
        user = self.user_repo.get_by_email(body.email)
        password_verified = verify_password(body.password, user.password_hash) if user else False

        if not user or not password_verified:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        self._ensure_team_link(user)

        token = create_access_token(data={"sub": str(user.id), "role": user.role.value if hasattr(user.role, 'value') else str(user.role)})
        user_teams = self.team_repo.get_by_user_id(user.id)
        team = user_teams[0] if user_teams else None

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=UserInfo(
                id=str(user.id),
                username=user.username,
                email=user.email,
                role=user.role,
                team_id=str(team.id) if team else None,
                team_name=team.name if team else None,
            ),
        )

    def forgot_password(self, body: ForgotPasswordRequest) -> ForgotPasswordResponse:
        user = self.user_repo.get_by_email(body.email)
        if not user:
            return ForgotPasswordResponse(
                message="If an account exists with that email, a password reset code has been sent."
            )

        otp = "".join(secrets.choice("0123456789") for _ in range(6))
        otp_hash = hash_password(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        self.otp_repo.create(
            user_id=user.id,
            otp_hash=otp_hash,
            expires_at=expires_at,
            used=False,
        )

        EmailService().send_reset_password_otp(
            to_email=user.email,
            name=user.username,
            otp_code=otp,
            expiry_minutes=10,
        )

        return ForgotPasswordResponse(
            message="If an account exists with that email, a password reset code has been sent."
        )

    def reset_password(self, body: ResetPasswordRequest) -> ResetPasswordResponse:
        user = self.user_repo.get_by_email(body.email)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset code.")

        otp_record = self.otp_repo.get_latest_unused_by_user(user.id)
        if not otp_record:
            raise HTTPException(status_code=400, detail="Invalid or expired reset code.")

        # Handle naive vs aware datetime issues by checking timezone info
        now_dt = datetime.now(timezone.utc)
        if otp_record.expires_at.tzinfo is None:
            now_dt = datetime.now()

        if now_dt > otp_record.expires_at:
            raise HTTPException(status_code=400, detail="Reset code has expired. Please request a new one.")

        if not verify_password(body.otp, otp_record.otp_hash):
            raise HTTPException(status_code=400, detail="Invalid or expired reset code.")

        self.user_repo.update(user, password_hash=hash_password(body.new_password))
        self.otp_repo.update(otp_record, used=True)

        return ResetPasswordResponse(
            message="Password has been reset successfully. You can now sign in with your new password."
        )

    def get_me(self, current_user: UserModel) -> UserResponse:
        user_teams = self.team_repo.get_by_user_id(current_user.id)
        team = user_teams[0] if user_teams else None
        response = UserResponse(
            id=str(current_user.id),
            username=current_user.username,
            email=current_user.email,
            role=current_user.role,
            created_at=current_user.created_at.isoformat(),
        )
        if team:
            response.team_id = str(team.id)
            response.team_name = team.name
        return response

    def admin_create_user(
        self, body: AdminCreateUserRequest, background_tasks: BackgroundTasks
    ) -> AdminCreateUserResponse:
        email_err = validate_email_domain(body.email)
        if email_err:
            raise HTTPException(status_code=422, detail=email_err)

        if self.user_repo.get_by_username(body.username):
            raise HTTPException(status_code=409, detail="Username already taken")

        if self.user_repo.get_by_email(body.email):
            raise HTTPException(status_code=409, detail="Email already registered")

        temp_password = _generate_temporary_password()

        user = UserModel(
            username=body.username,
            email=body.email.lower(),
            password_hash=hash_password(temp_password),
            role=UserRole.TEAM_LEADER,
            is_active=True,
        )
        user = self.user_repo.create(**{
            "username": user.username,
            "email": user.email,
            "password_hash": user.password_hash,
            "role": user.role,
            "is_active": user.is_active,
        })

        team_val = body.team_name.strip().upper()
        team_letter = re.sub(r"^TEAM[\s_]*", "", team_val)
        if team_letter not in ["A", "B", "C", "D", "E"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid team. Only Teams A, B, C, D, E are allowed.",
            )

        existing_team = self.team_repo.get_by_code(team_letter)
        if existing_team:
            if existing_team.user_id is not None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Team '{team_letter}' already has a registered team leader.",
                )
            existing_team.user_id = user.id
            existing_team.team_leader_name = body.team_leader_name
            self.team_repo.save(existing_team)
            team = existing_team
        else:
            team = TeamModel(
                team_id=team_letter,
                name=f"Team {team_letter}",
                code=team_letter,
                team_leader_name=body.team_leader_name,
                user_id=user.id,
            )
            team = self.team_repo.create(team)

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
            role=user.role.value if hasattr(user.role, 'value') else str(user.role),
            team_id=str(team.id),
            team_name=team.name,
        )
