import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.enums import MatchStatus


class MatchModel(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    home_team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    away_team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    freeze_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    round: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[MatchStatus] = mapped_column(
        SAEnum(MatchStatus, name="match_status", create_constraint=True),
        nullable=False,
        default=MatchStatus.SCHEDULED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # External API Fields — only set for API-imported matches; NULL for manual matches
    external_api_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    competition_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_sync_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

