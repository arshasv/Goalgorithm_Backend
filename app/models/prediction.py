import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import Index

from app.database.base import Base
from app.models.enums import FirstGoalTeam, PredictionStatus, Winner


class PredictionModel(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # FIX:
    # Database columns are VARCHAR, not UUID
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teams.id", ondelete="RESTRICT"),
        nullable=False
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("matches.id", ondelete="RESTRICT"),
        nullable=False
    )


    submission_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )


    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )


    status: Mapped[PredictionStatus] = mapped_column(
        SAEnum(
            PredictionStatus,
            name="prediction_status",
            create_constraint=True
        ),
        nullable=False,
        default=PredictionStatus.PENDING_VALIDATION,
    )


    # --------------------------
    # Win probabilities
    # --------------------------

    predicted_winner: Mapped[Winner] = mapped_column(
        SAEnum(
            Winner,
            name="winner_enum",
            create_constraint=True
        ),
        nullable=False
    )


    home_win_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


    draw_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


    away_win_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


    # --------------------------
    # Score prediction
    # --------------------------

    predicted_home_goals: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )


    predicted_away_goals: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )


    total_goals_prediction: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )



    # --------------------------
    # Goal insights
    # --------------------------

    both_teams_to_score_prediction: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )


    both_teams_to_score_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


    first_goal_team: Mapped[FirstGoalTeam | None] = mapped_column(
        SAEnum(
            FirstGoalTeam,
            name="first_goal_team_enum",
            create_constraint=True
        ),
        nullable=True
    )


    first_goal_team_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


    clean_sheet_predictions: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )


    home_clean_sheet_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


    away_clean_sheet_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


    goal_scorers: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )


    raw_payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )


    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )



    player_predictions = relationship(
        "PlayerPredictionModel",
        back_populates="prediction",
        cascade="all, delete-orphan",
        primaryjoin="PlayerPredictionModel.prediction_id == PredictionModel.id",
    )


    __table_args__ = (
        Index(
            "ix_predictions_team_match",
            "team_id",
            "match_id",
            unique=True
        ),
        Index(
            "ix_predictions_match_id",
            "match_id"
        ),
        Index(
            "ix_predictions_team_id",
            "team_id"
        ),
    )



class PlayerPredictionModel(Base):

    __tablename__ = "player_predictions"


    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )


    prediction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("predictions.id"),
        nullable=False
    )


    player_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )


    team: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )


    predicted_goals: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )


    goal_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


    player_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )


    assist_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


    prediction = relationship(
        "PredictionModel",
        back_populates="player_predictions"
    )


    __table_args__ = (
        Index(
            "ix_player_predictions_prediction_id",
            "prediction_id"
        ),
    )