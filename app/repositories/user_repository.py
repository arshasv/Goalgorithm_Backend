from sqlalchemy import select
from sqlalchemy.orm import Session
import uuid
from app.models.user import UserModel
from app.models.password_reset_otp import PasswordResetOtpModel
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, UserModel)

    def get_by_username(self, username: str) -> UserModel | None:
        return self.db.execute(
            select(UserModel).where(UserModel.username == username)
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> UserModel | None:
        return self.db.execute(
            select(UserModel).where(UserModel.email == email.lower())
        ).scalar_one_or_none()


class PasswordResetOtpRepository(BaseRepository[PasswordResetOtpModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PasswordResetOtpModel)

    def get_latest_unused_by_user(self, user_id: uuid.UUID) -> PasswordResetOtpModel | None:
        return self.db.execute(
            select(PasswordResetOtpModel)
            .where(
                PasswordResetOtpModel.user_id == user_id,
                PasswordResetOtpModel.used.is_(False),
            )
            .order_by(PasswordResetOtpModel.created_at.desc())
        ).scalars().first()
