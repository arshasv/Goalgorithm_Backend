import logging
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user

from app.auth.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)

from app.database.session import get_db

from app.utils.email_validator import validate_email_domain

from app.models.enums import UserRole
from app.models.password_reset_otp import PasswordResetOtpModel
from app.models.team import TeamModel
from app.models.user import UserModel

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


logger = logging.getLogger(__name__)


def _extract_team_code(email: str, team_name: str | None = None) -> str | None:
    local_part = email.lower().split("@")[0].strip()
    match = re.match(r'^team(\w+)$', local_part)
    if match:
        return match.group(1).upper()
    if team_name:
        val = team_name.strip().upper()
        return re.sub(r'^TEAM[\s_]*', '', val)
    return None


def _ensure_team_link(user: UserModel, db: Session) -> TeamModel | None:
    if user.role != "TEAM_LEADER":
        return None
    team = db.query(TeamModel).filter(TeamModel.user_id == user.id).first()
    if team:
        return team
    team_code = _extract_team_code(user.email, None)
    if not team_code:
        return None
    team = db.query(TeamModel).filter(TeamModel.team_id == team_code).first()
    if team and team.user_id is None:
        team.user_id = user.id
        db.commit()
        return team
    return None


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    status_code=201,
    response_model=RegisterResponse,
)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
):

    email_err = validate_email_domain(
        body.email
    )

    if email_err:
        raise HTTPException(
            status_code=422,
            detail=email_err,
        )


    if (
        db.query(UserModel)
        .filter(
            UserModel.username == body.username
        )
        .first()
    ):
        raise HTTPException(
            status_code=409,
            detail="Username already taken",
        )


    if (
        db.query(UserModel)
        .filter(
            UserModel.email == body.email.lower()
        )
        .first()
    ):
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )


    user = UserModel(
        username=body.username,
        email=body.email.lower(),
        password_hash=hash_password(
            body.password
        ),
        role=UserRole.TEAM_LEADER,
        is_active=True,
    )


    db.add(user)
    db.flush()

    team_code = _extract_team_code(body.email, body.team_name)
    if not team_code:
        raise HTTPException(
            status_code=400,
            detail="Could not determine team code. Use an email like teamX@domain.com or provide team_name."
        )

    team = db.query(TeamModel).filter(TeamModel.team_id == team_code).first()
    if team:
        if team.user_id is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Team '{team_code}' already has a registered team leader."
            )
        team.user_id = user.id
        team.team_leader_name = body.team_leader_name
    else:
        team = TeamModel(
            team_id=team_code,
            name=f"Team {team_code}",
            code=team_code,
            team_leader_name=body.team_leader_name,
            user_id=user.id,
        )
        db.add(team)

    db.commit()

    db.refresh(user)
    db.refresh(team)


    token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
        }
    )


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



@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
):

    print("LOGIN DEBUG email:", body.email)
    user = (
        db.query(UserModel)
        .filter(
            UserModel.email == body.email.lower()
        )
        .first()
    )

    print("LOGIN DEBUG user found:", user is not None)
    if user:
        print("LOGIN DEBUG user.id:", user.id)
        print("LOGIN DEBUG user.email:", user.email)
        print("LOGIN DEBUG user.role:", user.role)
        # user doesn't have is_active, but let's check it if it does
        print("LOGIN DEBUG stored hash exists:", bool(user.password_hash))
        
        password_verified = verify_password(body.password, user.password_hash)
        print("LOGIN DEBUG password ok:", password_verified)
    else:
        password_verified = False

    if (
        not user
        or not password_verified
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    _ensure_team_link(user, db)

    token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
        }
    )

    team = (
        db.query(TeamModel)
        .filter(
            TeamModel.user_id == user.id
        )
        .first()
    )


    return LoginResponse(
        access_token=token,
        token_type="bearer",

        user=UserInfo(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,

            team_id=str(team.id)
            if team
            else None,

            team_name=team.name
            if team
            else None,
        ),
    )



@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(UserModel)
        .filter(UserModel.email == body.email.lower())
        .first()
    )

    if not user:
        return ForgotPasswordResponse(
            message="If an account exists with that email, a password reset code has been sent."
        )

    secrets = __import__("secrets")
    otp = "".join(secrets.choice("0123456789") for _ in range(6))

    from app.auth.auth_service import hash_password as _hp
    otp_hash = _hp(otp)

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    otp_record = PasswordResetOtpModel(
        user_id=user.id,
        otp_hash=otp_hash,
        expires_at=expires_at,
        used=False,
    )
    db.add(otp_record)
    db.commit()

    from app.email.service import EmailService
    EmailService().send_reset_password_otp(
        to_email=user.email,
        name=user.username,
        otp_code=otp,
        expiry_minutes=10,
    )

    return ForgotPasswordResponse(
        message="If an account exists with that email, a password reset code has been sent."
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
)
def reset_password(
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(UserModel)
        .filter(UserModel.email == body.email.lower())
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset code.",
        )

    otp_record = (
        db.query(PasswordResetOtpModel)
        .filter(
            PasswordResetOtpModel.user_id == user.id,
            PasswordResetOtpModel.used == False,
        )
        .order_by(PasswordResetOtpModel.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset code.",
        )

    if datetime.now(timezone.utc) > otp_record.expires_at:
        raise HTTPException(
            status_code=400,
            detail="Reset code has expired. Please request a new one.",
        )

    if not verify_password(body.otp, otp_record.otp_hash):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset code.",
        )

    user.password_hash = hash_password(body.new_password)
    otp_record.used = True
    db.commit()

    return ResetPasswordResponse(
        message="Password has been reset successfully. You can now sign in with your new password."
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def read_users_me(
    current_user: UserModel = Depends(
        get_current_user
    ),
):

    response = UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at.isoformat(),
    )


    if current_user.team:

        response.team_id = str(
            current_user.team.id
        )

        response.team_name = (
            current_user.team.name
        )


    return response



@router.get(
    "/profile",
    response_model=UserResponse,
)
def read_profile(
    current_user: UserModel = Depends(
        get_current_user
    ),
):

    return read_users_me(
        current_user=current_user
    )