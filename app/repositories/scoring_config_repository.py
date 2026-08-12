from sqlalchemy import select
from sqlalchemy.orm import Session
import uuid
from app.models.scoring_config import ScoringConfigModel
from app.repositories.base_repository import BaseRepository

class ScoringConfigRepository(BaseRepository[ScoringConfigModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ScoringConfigModel)

    def get_active(self) -> ScoringConfigModel | None:
        return self.db.execute(
            select(ScoringConfigModel).where(ScoringConfigModel.is_active.is_(True))
        ).scalars().first()

    def get_all_by_created(self) -> list[ScoringConfigModel]:
        return list(
            self.db.execute(
                select(ScoringConfigModel).order_by(ScoringConfigModel.created_at.desc())
            )
            .scalars()
            .all()
        )

    def get_latest_version(self) -> ScoringConfigModel | None:
        return self.db.execute(
            select(ScoringConfigModel).order_by(ScoringConfigModel.version.desc())
        ).scalars().first()

    def deactivate_all(self) -> None:
        self.db.query(ScoringConfigModel).filter(
            ScoringConfigModel.is_active.is_(True)
        ).update({"is_active": False})
        self.db.flush()

    def deactivate_all_except(self, except_id: uuid.UUID) -> None:
        self.db.query(ScoringConfigModel).filter(
            ScoringConfigModel.is_active.is_(True),
            ScoringConfigModel.id != except_id,
        ).update({"is_active": False})
        self.db.flush()
