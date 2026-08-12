from pydantic import BaseModel, Field


class TechnicalEvaluation(BaseModel):
    team_id: str = Field(..., min_length=1)
    code_quality: int = Field(..., ge=0, le=5)
    backend_quality: int = Field(..., ge=0, le=5)
    teamwork: int = Field(..., ge=0, le=5)
    ai_explanation: int = Field(..., ge=0, le=5)
