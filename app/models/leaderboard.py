import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import Index

from app.database.base import Base


class LeaderboardModel(Base):
    __tablename__ = "leaderboard"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phase1_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    presentation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_leaderboard_team_id", "team_id", unique=True),
        Index("ix_leaderboard_rank", "rank"),
    )
