from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List


class FinalScore(BaseModel):
    home_team_goals: int = Field(..., ge=0)
    away_team_goals: int = Field(..., ge=0)


class PlayerResult(BaseModel):
    player_id: str = Field(..., min_length=1)
    player_name: str = Field(..., min_length=1)
    actual_goals: int = Field(..., ge=0)


class GoalScorers(BaseModel):
    home: List[str] = Field(default_factory=list)
    away: List[str] = Field(default_factory=list)


import uuid

class ActualResultSubmission(BaseModel):
    match_id: uuid.UUID
    actual_winner: str
    final_score: FinalScore
    goal_scorers: GoalScorers = Field(default_factory=GoalScorers)
    player_results: List[PlayerResult]
    first_team_to_score: str = "none"

    @field_validator("first_team_to_score")
    @classmethod
    def validate_first_team_to_score(cls, v: str) -> str:
        allowed = {"home", "away", "none"}
        if v.lower() not in allowed:
            raise ValueError(f"first_team_to_score must be one of {allowed}")
        return v.lower()

    @field_validator("actual_winner")
    @classmethod
    def validate_winner(cls, v: str) -> str:
        allowed = {"home", "away", "draw"}
        if v.lower() not in allowed:
            raise ValueError(f"actual_winner must be one of {allowed}")
        return v.lower()

    @field_validator("player_results")
    @classmethod
    def validate_player_list(cls, v: List[PlayerResult]) -> List[PlayerResult]:
        if not v:
            raise ValueError("player_results cannot be empty")
        return v

    @model_validator(mode="after")
    def validate_goal_scorers(self):
        home_count = len(self.goal_scorers.home)
        away_count = len(self.goal_scorers.away)
        expected_home = self.final_score.home_team_goals
        expected_away = self.final_score.away_team_goals
        if home_count != expected_home:
            raise ValueError(
                f"Number of home goal scorers ({home_count}) must equal actual home goals ({expected_home})"
            )
        if away_count != expected_away:
            raise ValueError(
                f"Number of away goal scorers ({away_count}) must equal actual away goals ({expected_away})"
            )
        return self
