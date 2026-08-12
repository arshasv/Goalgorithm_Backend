import uuid
from pathlib import Path
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.team import TeamModel
from app.models.model_submission import ModelSubmissionModel
from app.schemas.model_submission_schema import MODEL_EXTENSIONS
from app.repositories.model_submission_repository import ModelSubmissionRepository
from app.repositories.team_repository import TeamRepository
from app.services.upload_window_service import UploadWindowService

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "models"
MAX_FILE_SIZE = 50 * 1024 * 1024

class ModelSubmissionService:
    def __init__(
        self,
        submission_repo: ModelSubmissionRepository,
        team_repo: TeamRepository,
        window_service: UploadWindowService,
    ) -> None:
        self.submission_repo = submission_repo
        self.team_repo = team_repo
        self.window_service = window_service

    def _ensure_upload_dir(self) -> None:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def _validate_model_file(self, filename: str, file_size: int) -> str:
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

    def _save_file(self, team_id: uuid.UUID, file: UploadFile, ext: str) -> str:
        self._ensure_upload_dir()
        team_dir = UPLOAD_DIR / str(team_id)
        team_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid.uuid4()}{ext}"
        dest = team_dir / unique_name
        with open(dest, "wb") as f:
            f.write(file.file.read())
        return str(dest)

    def upload_model(self, file: UploadFile, team: TeamModel) -> ModelSubmissionModel:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        window = self.window_service.get_or_create_window()
        if not window or not window.is_enabled:
            raise HTTPException(status_code=403, detail="Model submission window closed")

        now = datetime.now(timezone.utc)
        if window.start_time and now < window.start_time:
            raise HTTPException(status_code=403, detail="Model submission window closed")
        if window.end_time and now > window.end_time:
            raise HTTPException(status_code=403, detail="Model submission window closed")

        ext = self._validate_model_file(file.filename, file.size or 0)
        self.submission_repo.deactivate_previous(team.id)

        file_path = self._save_file(team.id, file, ext)
        submission = ModelSubmissionModel(
            team_id=team.id,
            file_name=file.filename,
            file_type=ext,
            file_path=file_path,
            file_size=file.size or 0,
            is_active=True,
        )
        return self.submission_repo.create(**{
            "team_id": submission.team_id,
            "file_name": submission.file_name,
            "file_type": submission.file_type,
            "file_path": submission.file_path,
            "file_size": submission.file_size,
            "is_active": submission.is_active,
        })

    def get_my_model(self, team: TeamModel) -> ModelSubmissionModel | None:
        return self.submission_repo.get_active_by_team(team.id)

    def list_my_models(self, team: TeamModel) -> tuple[list[ModelSubmissionModel], int]:
        submissions = self.submission_repo.get_all_by_team(team.id)
        return submissions, len(submissions)

    def list_all_submissions(self) -> tuple[list[ModelSubmissionModel], int]:
        submissions = self.submission_repo.get_all_desc()
        return submissions, len(submissions)

    def get_team_submission(self, team_id: uuid.UUID) -> ModelSubmissionModel | None:
        if not self.team_repo.get_by_id(team_id):
            raise HTTPException(status_code=404, detail="Team not found")
        return self.submission_repo.get_active_by_team(team_id)

    def get_submission_download(self, submission_id: uuid.UUID) -> ModelSubmissionModel:
        submission = self.submission_repo.get(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        file_path = Path(submission.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Uploaded model file not found")

        return submission
