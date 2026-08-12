from sqlalchemy.orm import Session
from app.models.upload_window import UploadWindowModel
from app.repositories.base_repository import BaseRepository

class UploadWindowRepository(BaseRepository[UploadWindowModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, UploadWindowModel)

    def get_first(self) -> UploadWindowModel | None:
        return self.db.query(UploadWindowModel).first()
