from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.team import TeamModel
from app.repositories.base_repository import BaseRepository


class TeamRepository(BaseRepository[TeamModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TeamModel)

    def get_by_code(self, code: str) -> TeamModel | None:
        return self.db.execute(
            select(TeamModel).where(TeamModel.code == code)
        ).scalar_one_or_none()

    def get_active(self) -> list[TeamModel]:
        return list(
            self.db.execute(
                select(TeamModel).where(TeamModel.is_active.is_(True))
            )
            .scalars()
            .all()
        )
