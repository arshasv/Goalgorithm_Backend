from sqlalchemy import select
from sqlalchemy.orm import Session
import uuid
from app.models.model_submission import ModelSubmissionModel
from app.repositories.base_repository import BaseRepository

class ModelSubmissionRepository(BaseRepository[ModelSubmissionModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ModelSubmissionModel)

    def deactivate_previous(self, team_id: uuid.UUID) -> None:
        self.db.query(ModelSubmissionModel).filter(
            ModelSubmissionModel.team_id == team_id,
            ModelSubmissionModel.is_active.is_(True),
        ).update({"is_active": False})
        self.db.flush()

    def get_active_by_team(self, team_id: uuid.UUID) -> ModelSubmissionModel | None:
        return self.db.execute(
            select(ModelSubmissionModel)
            .where(
                ModelSubmissionModel.team_id == team_id,
                ModelSubmissionModel.is_active.is_(True),
            )
            .order_by(ModelSubmissionModel.uploaded_at.desc())
        ).scalars().first()

    def get_all_by_team(self, team_id: uuid.UUID) -> list[ModelSubmissionModel]:
        return list(
            self.db.execute(
                select(ModelSubmissionModel)
                .where(ModelSubmissionModel.team_id == team_id)
                .order_by(ModelSubmissionModel.uploaded_at.desc())
            )
            .scalars()
            .all()
        )

    def get_all_desc(self) -> list[ModelSubmissionModel]:
        return list(
            self.db.execute(
                select(ModelSubmissionModel).order_by(ModelSubmissionModel.uploaded_at.desc())
            )
            .scalars()
            .all()
        )
