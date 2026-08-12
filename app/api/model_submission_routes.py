import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_current_team, get_current_team_leader
from app.database.session import get_db
from app.models.model_submission import ModelSubmissionModel
from app.models.upload_window import UploadWindowModel
from app.models.team import TeamModel
from app.models.user import UserModel
from datetime import datetime, timezone
from app.schemas.model_submission_schema import (
    MODEL_EXTENSIONS,
    ModelSubmissionListResponse,
    ModelSubmissionResponse,
)

team_model_router = APIRouter(prefix="/teams", tags=["model-submission"])
admin_model_router = APIRouter(prefix="/admin/models", tags=["model-submission"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "models"
MAX_FILE_SIZE = 50 * 1024 * 1024


def _ensure_upload_dir():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _validate_model_file(filename: str, file_size: int) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in MODEL_EXTENSIONS:
        allowed = ", ".join(sorted(MODEL_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {allowed}",
        )
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({file_size / 1024 / 1024:.1f} MB). Maximum: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB",
        )
    return ext


def _save_file(team_id: uuid.UUID, file: UploadFile, ext: str) -> str:
    _ensure_upload_dir()
    team_dir = UPLOAD_DIR / str(team_id)
    team_dir.mkdir(parents=True, exist_ok=True, mode=0o777)
    unique_name = f"{uuid.uuid4()}{ext}"
    dest = team_dir / unique_name
    with open(dest, "wb") as f:
        f.write(file.file.read())
    return str(dest)


def _deactivate_previous(team_id: uuid.UUID, db: Session):
    db.query(ModelSubmissionModel).filter(
        ModelSubmissionModel.team_id == team_id,
        ModelSubmissionModel.is_active.is_(True),
    ).update({"is_active": False})
    db.flush()


@team_model_router.post("/my-team/model", response_model=ModelSubmissionResponse)
def upload_model(
    file: UploadFile = File(...),
    team: TeamModel = Depends(get_current_team),
    _user: UserModel = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    window = db.query(UploadWindowModel).first()
    if not window or not window.is_enabled:
        raise HTTPException(status_code=403, detail="Model submission window closed")
    
    now = datetime.now(timezone.utc)
    if window.start_time and now < window.start_time:
        raise HTTPException(status_code=403, detail="Model submission window closed")
    if window.end_time and now > window.end_time:
        raise HTTPException(status_code=403, detail="Model submission window closed")

    ext = _validate_model_file(file.filename, file.size or 0)
    _deactivate_previous(team.id, db)

    file_path = _save_file(team.id, file, ext)
    submission = ModelSubmissionModel(
        team_id=team.id,
        file_name=file.filename,
        file_type=ext,
        file_path=file_path,
        file_size=file.size or 0,
        is_active=True,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@team_model_router.get("/my-team/model", response_model=ModelSubmissionResponse | None)
def get_my_model(
    team: TeamModel = Depends(get_current_team),
    _user: UserModel = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    return db.query(ModelSubmissionModel).filter(
        ModelSubmissionModel.team_id == team.id,
        ModelSubmissionModel.is_active.is_(True),
    ).order_by(ModelSubmissionModel.uploaded_at.desc()).first()


@team_model_router.get("/my-team/models", response_model=ModelSubmissionListResponse)
def list_my_models(
    team: TeamModel = Depends(get_current_team),
    _user: UserModel = Depends(get_current_team_leader),
    db: Session = Depends(get_db),
):
    submissions = db.query(ModelSubmissionModel).filter(
        ModelSubmissionModel.team_id == team.id
    ).order_by(ModelSubmissionModel.uploaded_at.desc()).all()
    return ModelSubmissionListResponse(submissions=submissions, total=len(submissions))



@admin_model_router.get("", response_model=ModelSubmissionListResponse)
def list_all_submissions(
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    submissions = db.query(ModelSubmissionModel).order_by(
        ModelSubmissionModel.uploaded_at.desc()
    ).all()
    return ModelSubmissionListResponse(submissions=submissions, total=len(submissions))


@admin_model_router.get("/team/{team_id}", response_model=ModelSubmissionResponse | None)
def get_team_submission(
    team_id: uuid.UUID,
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    if not db.query(TeamModel).filter(TeamModel.id == team_id).first():
        raise HTTPException(status_code=404, detail="Team not found")
    return db.query(ModelSubmissionModel).filter(
        ModelSubmissionModel.team_id == team_id,
        ModelSubmissionModel.is_active.is_(True),
    ).order_by(ModelSubmissionModel.uploaded_at.desc()).first()


@admin_model_router.get("/{submission_id}/download")
def download_model(
    submission_id: uuid.UUID,
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    submission = db.query(ModelSubmissionModel).filter(
        ModelSubmissionModel.id == submission_id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    file_path = Path(submission.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded model file not found")

    from starlette.responses import FileResponse
    return FileResponse(path=str(file_path), filename=submission.file_name, media_type="application/octet-stream")
