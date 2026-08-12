import os
import shutil
import uuid
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, BackgroundTasks

from app.model_execution.models.model_upload import ModelUploadModel
from app.model_execution.models.model_execution import ModelExecutionModel
from app.model_execution.services.model_executor import ModelExecutor

UPLOAD_DIR = "/tmp/model_uploads"

class ExecutionService:
    def __init__(self, db: Session):
        self.db = db

    def upload_model(self, team_id: uuid.UUID, match_id: uuid.UUID, file: UploadFile) -> dict:
        if not file.filename.endswith('.pkl'):
            raise HTTPException(status_code=400, detail="Only .pkl files are allowed")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        model_upload = ModelUploadModel(
            team_id=team_id,
            match_id=match_id,
            original_filename=file.filename,
            stored_file_path=file_path,
            status="IDLE"
        )
        self.db.add(model_upload)
        self.db.commit()
        self.db.refresh(model_upload)

        return {
            "model_id": model_upload.id,
            "status": model_upload.status
        }

    def get_execution_status(self, execution_id: uuid.UUID) -> dict:
        # Check executions first
        execution = self.db.query(ModelExecutionModel).filter(ModelExecutionModel.id == execution_id).first()
        if not execution:
            # Maybe they passed the model_upload_id
            execution = self.db.query(ModelExecutionModel).filter(ModelExecutionModel.model_upload_id == execution_id).first()
            if not execution:
                upload = self.db.query(ModelUploadModel).filter(ModelUploadModel.id == execution_id).first()
                if not upload:
                    raise HTTPException(status_code=404, detail="Execution not found")
                return {
                    "status": upload.status,
                    "error_message": None,
                    "prediction_id": None
                }
        
        return {
            "status": execution.status,
            "error_message": execution.error_message,
            "prediction_id": execution.prediction_id
        }

    def execute_model(self, model_id: uuid.UUID, background_tasks: BackgroundTasks) -> dict:
        upload = self.db.query(ModelUploadModel).filter(ModelUploadModel.id == model_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Model upload not found")

        execution = ModelExecutionModel(
            model_upload_id=model_id,
            status="RUNNING"
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        executor = ModelExecutor(execution.id)
        background_tasks.add_task(executor.execute_in_background)

        return {
            "execution_id": execution.id,
            "status": execution.status
        }
