from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.upload_window import UploadWindowModel
from app.repositories.upload_window_repository import UploadWindowRepository
from app.schemas.upload_window_schema import UploadWindowUpdate

class UploadWindowService:
    def __init__(self, repository: UploadWindowRepository) -> None:
        self.repository = repository

    def get_or_create_window(self) -> UploadWindowModel:
        window = self.repository.get_first()
        if not window:
            window = self.repository.create(is_enabled=False)
        return window

    def update_upload_window(self, update_data: UploadWindowUpdate) -> UploadWindowModel:
        window = self.get_or_create_window()
        return self.repository.update(
            window,
            is_enabled=update_data.is_enabled,
            start_time=update_data.start_time,
            end_time=update_data.end_time,
        )
