from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class MatchCreate(BaseModel):
    match_number: int
    home_team_name: str
    away_team_name: str
    scheduled_at: datetime
    freeze_deadline: Optional[datetime] = None
    round: Optional[str] = None

    @field_validator("home_team_name", "away_team_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Team name must not be empty")
        return v


class MatchUpdate(BaseModel):
    home_team_name: Optional[str] = None
    away_team_name: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    freeze_deadline: Optional[datetime] = None
    round: Optional[str] = None


class MatchResponse(BaseModel):
    id: uuid.UUID
    match_number: int
    home_team_name: str
    away_team_name: str
    scheduled_at: datetime
    freeze_deadline: datetime
    status: str
    round: Optional[str] = None
    created_at: datetime
    external_api_id: Optional[str] = None
    competition_name: Optional[str] = None
    external_sync_status: Optional[str] = None

    model_config = {"from_attributes": True}
