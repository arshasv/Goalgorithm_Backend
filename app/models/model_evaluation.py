import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Uuid, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ModelEvaluationModel(Base):
    __tablename__ = "model_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("model_submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    overall_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    winner_prediction_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    scoreline_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    probability_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    player_prediction_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    matches_tested: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    strength_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weakness_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evaluation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
