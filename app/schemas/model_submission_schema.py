import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


MODEL_EXTENSIONS: set[str] = {
    ".pkl", ".pickle", ".pt", ".pth", ".h5",
    ".joblib", ".onnx", ".sav",
}


class ModelSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
    team_name: str | None = None
    model_name: str | None = None
    file_name: str
    file_type: str
    file_size: int
    version: int
    model_type: str | None = None
    description: str | None = None
    notes: str | None = None
    status: str
    is_active: bool
    uploaded_at: datetime


class ModelSubmissionListResponse(BaseModel):
    submissions: list[ModelSubmissionResponse]
    total: int
