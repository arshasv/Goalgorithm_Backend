from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class PresentationRoundCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class PresentationRoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    created_at: datetime
