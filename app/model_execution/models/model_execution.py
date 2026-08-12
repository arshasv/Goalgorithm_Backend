import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
import pandas as pd
import numpy as np
import joblib
import cloudpickle
import lightgbm as lgb
import xgboost as xgb

class ModelExecutionModel(Base):
    __tablename__ = "model_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    model_upload_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("model_uploads.id"))
    status: Mapped[str] = mapped_column(String(50), default="IDLE")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    prediction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("predictions.id"), nullable=True)

    model_upload = relationship("ModelUploadModel", back_populates="executions")
