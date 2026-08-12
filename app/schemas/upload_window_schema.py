from datetime import datetime
import uuid

from pydantic import BaseModel, Field


class UploadWindowBase(BaseModel):
    is_enabled: bool = Field(default=False)
    start_time: datetime | None = None
    end_time: datetime | None = None


class UploadWindowUpdate(UploadWindowBase):
    pass


class UploadWindowResponse(UploadWindowBase):
    id: uuid.UUID
    updated_at: datetime

    class Config:
        from_attributes = True
