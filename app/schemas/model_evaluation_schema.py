import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ModelEvaluationCreate(BaseModel):
    model_id: uuid.UUID
    overall_accuracy: float | None = None
    winner_prediction_accuracy: float | None = None
    scoreline_accuracy: float | None = None
    probability_accuracy: float | None = None
    player_prediction_accuracy: float | None = None
    matches_tested: int | None = None
    average_score: float | None = None
    final_ai_score: float | None = None
    evaluation_notes: str | None = None


class ModelEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model_id: uuid.UUID
    team_id: uuid.UUID
    overall_accuracy: float | None = None
    winner_prediction_accuracy: float | None = None
    scoreline_accuracy: float | None = None
    probability_accuracy: float | None = None
    player_prediction_accuracy: float | None = None
    matches_tested: int | None = None
    average_score: float | None = None
    final_ai_score: float | None = None
    strength_category: str | None = None
    weakness_category: str | None = None
    evaluation_notes: str | None = None
    evaluated_at: datetime


class AnalyticsTeamScore(BaseModel):
    team_name: str
    overall_accuracy: float | None = None
    winner_prediction_accuracy: float | None = None
    scoreline_accuracy: float | None = None
    probability_accuracy: float | None = None
    player_prediction_accuracy: float | None = None
    final_ai_score: float | None = None
    version: int | None = None


class ModelEvaluationAnalyticsResponse(BaseModel):
    team_rankings: list[AnalyticsTeamScore]
    model_scores: list[AnalyticsTeamScore]
    accuracy_comparison: list[AnalyticsTeamScore]
    category_breakdown: list[AnalyticsTeamScore]
    version_history: list[dict] # { "team_name": str, "history": [ { "version": 1, "accuracy": 60 } ] }
