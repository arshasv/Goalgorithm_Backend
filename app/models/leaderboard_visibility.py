import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LeaderboardVisibilityModel(Base):
    __tablename__ = "leaderboard_visibility"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    show_all_teams_leaderboard: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_rank: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_team_name: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_phase_scores: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_phase_1_score: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_technical_score: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_presentation_score: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_final_score: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_total_points: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_score_breakdown: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_predictions_count: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    show_correct_predictions: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    analytics_visibility_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    show_model_analytics: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_prediction_analytics: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_technical_analytics: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_presentation_analytics: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_overall_comparison: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_judge_analytics: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_leaderboard_analytics: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
