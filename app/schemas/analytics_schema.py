from pydantic import BaseModel


class TopTeam(BaseModel):
    team_name: str
    final_score: float | None = None


class AverageScores(BaseModel):
    phase1_average: float | None = None
    technical_average: float | None = None
    presentation_average: float | None = None
    final_average: float | None = None


class OverviewResponse(BaseModel):
    total_teams: int
    top_team: TopTeam | None = None
    average_scores: AverageScores


class TeamModelAnalytics(BaseModel):
    team: str
    model_name: str | None = None
    accuracy: float | None = None
    total_predictions: int
    correct_predictions: int
    average_score: float | None = None


class CriterionAverage(BaseModel):
    criterion: str
    avg_score: float
    max_score: int


class StrengthWeakness(BaseModel):
    criterion: str
    score: float
    max_score: int
    pct: float


class CriteriaRankingEntry(BaseModel):
    team: str
    avg_score: float
    max_score: int


class CriteriaRanking(BaseModel):
    criterion: str
    rankings: list[CriteriaRankingEntry]
    best_team: str
    weakest_team: str


class TeamPresentationAnalytics(BaseModel):
    team: str
    strongest: StrengthWeakness | None = None
    weakest: StrengthWeakness | None = None
    criteria_averages: list[CriterionAverage]


class PresentationResponse(BaseModel):
    teams: list[TeamPresentationAnalytics]
    criteria_rankings: list[CriteriaRanking]


class ScoreBreakdown(BaseModel):
    total_predictions: int
    correct_predictions: int
    average_score: float | None = None
    winner_accuracy_pct: float | None = None


class LeaderboardEntry(BaseModel):
    rank: int | None = None
    phase1_score: float | None = None
    technical_score: float | None = None
    presentation_score: float | None = None
    final_score: float | None = None


class TeamAnalyticsResponse(BaseModel):
    team_name: str
    scores_breakdown: ScoreBreakdown
    leaderboard: LeaderboardEntry | None = None
    strengths: list[StrengthWeakness] = []
    weaknesses: list[StrengthWeakness] = []
