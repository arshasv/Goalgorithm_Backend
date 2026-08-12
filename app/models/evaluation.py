import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, Float, Integer, String, Uuid, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import Index

from app.database.base import Base
from app.models.enums import Grade


class TechnicalEvaluationModel(Base):
    __tablename__ = "technical_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    code_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    backend_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teamwork: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_explanation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_technical_evaluations_team_id", "team_id", unique=True),
    )


class PresentationEvaluationModel(Base):
    __tablename__ = "presentation_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    ai_explanation_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qa_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivery_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    presentation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade: Mapped[Grade | None] = mapped_column(
        SAEnum(Grade, name="grade_enum", create_constraint=True), nullable=True
    )
    multiplier: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    judge_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    judge_scores: Mapped[list | None] = mapped_column(JSON, nullable=True)
    presentation_criteria_config: Mapped[list | None] = mapped_column(JSON, nullable=True)
    max_marks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    round_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("presentation_rounds.id", ondelete="CASCADE"), nullable=True)

    __table_args__ = (
        Index("ix_presentation_evaluations_team_id", "team_id"),
        UniqueConstraint("team_id", "round_id", name="uq_team_presentation_round")
    )

