import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database.base import Base

VALID_TEAM_IDS = {"A", "B", "C", "D", "E"}


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    team_id: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    name_normalized: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    @validates("name")
    def validate_name(self, key, value):
        from app.utils.team_name_utils import normalize_team_name
        self.name_normalized = normalize_team_name(value)
        return value

    # short identifier matching team_id (A-E), kept for old API compat
    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    team_leader_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        server_default="",
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    is_csv_managed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )


    user = relationship(
        "UserModel",
        back_populates="team",
        uselist=False,
    )

    members = relationship(
        "TeamMemberModel",
        backref="team",
        cascade="all, delete-orphan",
    )