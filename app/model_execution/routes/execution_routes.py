import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_db
from app.models.user import UserModel
from app.model_execution.services.execution_service import ExecutionService
from app.model_execution.schemas.execution_schema import ModelUploadResponse, ModelExecutionStatusResponse, ModelExecutionResponse

router = APIRouter(prefix="/model-execution", tags=["model_execution"])

@router.post("/upload", response_model=ModelUploadResponse)
def upload_model(
    match_id: uuid.UUID = Form(...),
    team_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db)
):
    service = ExecutionService(db)
    result = service.upload_model(
        team_id=team_id,
        match_id=match_id,
        file=file
    )
    return result

@router.get("/{execution_id}/status", response_model=ModelExecutionStatusResponse)
def get_status(
    execution_id: uuid.UUID,
    current_organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db)
):
    service = ExecutionService(db)
    result = service.get_execution_status(execution_id)
    return result

@router.post("/{model_id}/execute", response_model=ModelExecutionResponse)
def execute_model(
    model_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db)
):
    service = ExecutionService(db)
    result = service.execute_model(model_id, background_tasks)
    return result
