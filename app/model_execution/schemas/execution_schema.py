import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ModelUploadResponse(BaseModel):
    model_id: uuid.UUID
    status: str

    model_config = ConfigDict(from_attributes=True)

class ModelExecutionResponse(BaseModel):
    execution_id: uuid.UUID
    status: str

    model_config = ConfigDict(from_attributes=True)

class ModelExecutionStatusResponse(BaseModel):
    status: str
    error_message: Optional[str] = None
    prediction_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)
