import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import Index

from app.database.base import Base
from app.models.enums import Winner


class ActualResultModel(Base):
    __tablename__ = "actual_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("matches.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    actual_winner: Mapped[Winner] = mapped_column(
        SAEnum(Winner, name="winner_enum", create_constraint=True), nullable=False
    )
    actual_home_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_away_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal_scorers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    first_team_to_score: Mapped[str] = mapped_column(String(50), default="none", nullable=False)
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    
    # External API Fields
    result_source: Mapped[str] = mapped_column(String(50), default="MANUAL", nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    player_actuals = relationship(
        "PlayerActualModel",
        back_populates="actual_result",
        cascade="all, delete-orphan",
        primaryjoin="PlayerActualModel.actual_result_id == ActualResultModel.id",
    )

    __table_args__ = (Index("ix_actual_results_match_id", "match_id", unique=True),)


class PlayerActualModel(Base):
    __tablename__ = "player_actuals"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actual_result_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("actual_results.id"),
        nullable=False,
    )
    player_id: Mapped[str] = mapped_column(String(255), nullable=False)
    player_name: Mapped[str] = mapped_column(String(255), nullable=False)
    actual_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)

    actual_result = relationship("ActualResultModel", back_populates="player_actuals")

    __table_args__ = (
        Index("ix_player_actuals_actual_result_id", "actual_result_id"),
    )
