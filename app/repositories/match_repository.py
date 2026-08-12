from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import MatchStatus
from app.models.match import MatchModel
from app.repositories.base_repository import BaseRepository


class MatchRepository(BaseRepository[MatchModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MatchModel)

    def get_by_match_number(self, match_number: int) -> MatchModel | None:
        return self.db.execute(
            select(MatchModel).where(MatchModel.match_number == match_number)
        ).scalar_one_or_none()

    def get_by_status(self, status: MatchStatus) -> list[MatchModel]:
        return list(
            self.db.execute(
                select(MatchModel).where(MatchModel.status == status)
            )
            .scalars()
            .all()
        )

    def get_frozen_or_later(self) -> list[MatchModel]:
        return list(
            self.db.execute(
                select(MatchModel).where(
                    MatchModel.status.in_(
                        [
                            MatchStatus.FROZEN,
                            MatchStatus.COMPLETED,
                            MatchStatus.RESULT_ENTERED,
                            MatchStatus.SCORED,
                        ]
                    )
                )
            )
            .scalars()
            .all()
        )
