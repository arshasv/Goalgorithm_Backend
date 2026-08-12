import uuid
from datetime import datetime

from pydantic import BaseModel


class LeaderboardVisibilityUpdate(BaseModel):
    show_all_teams_leaderboard: bool | None = None
    show_rank: bool | None = None
    show_team_name: bool | None = None
    show_phase_scores: bool | None = None
    show_phase_1_score: bool | None = None
    show_technical_score: bool | None = None
    show_presentation_score: bool | None = None
    show_final_score: bool | None = None
    show_total_points: bool | None = None
    show_score_breakdown: bool | None = None
    show_predictions_count: bool | None = None
    show_correct_predictions: bool | None = None
    analytics_visibility_enabled: bool | None = None
    show_model_analytics: bool | None = None
    show_prediction_analytics: bool | None = None
    show_technical_analytics: bool | None = None
    show_presentation_analytics: bool | None = None
    show_overall_comparison: bool | None = None
    show_judge_analytics: bool | None = None
    show_leaderboard_analytics: bool | None = None


class LeaderboardVisibilityResponse(BaseModel):
    id: uuid.UUID
    show_all_teams_leaderboard: bool
    show_rank: bool
    show_team_name: bool
    show_phase_scores: bool
    show_phase_1_score: bool
    show_technical_score: bool
    show_presentation_score: bool
    show_final_score: bool
    show_total_points: bool
    show_score_breakdown: bool
    show_predictions_count: bool
    show_correct_predictions: bool
    analytics_visibility_enabled: bool
    show_model_analytics: bool
    show_prediction_analytics: bool
    show_technical_analytics: bool
    show_presentation_analytics: bool
    show_overall_comparison: bool
    show_judge_analytics: bool
    show_leaderboard_analytics: bool
    updated_at: datetime

    class Config:
        from_attributes = True
