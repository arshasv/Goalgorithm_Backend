from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import (
    PresentationEvaluationModel,
    TechnicalEvaluationModel,
)
from app.models.leaderboard import LeaderboardModel
from app.repositories.base_repository import BaseRepository


class LeaderboardRepository(BaseRepository[LeaderboardModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, LeaderboardModel)

    def get_by_team(self, team_id: str) -> LeaderboardModel | None:
        return self.db.execute(
            select(LeaderboardModel).where(
                LeaderboardModel.team_id == team_id
            )
        ).scalar_one_or_none()

    def get_ranked(self) -> list[LeaderboardModel]:
        return list(
            self.db.execute(
                select(LeaderboardModel).order_by(LeaderboardModel.rank)
            )
            .scalars()
            .all()
        )

    def get_final(self) -> list[LeaderboardModel]:
        return list(
            self.db.execute(
                select(LeaderboardModel).where(
                    LeaderboardModel.is_final.is_(True)
                )
            )
            .scalars()
            .all()
        )


class TechnicalEvaluationRepository(BaseRepository[TechnicalEvaluationModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TechnicalEvaluationModel)

    def get_by_team(
        self, team_id: str
    ) -> TechnicalEvaluationModel | None:
        return self.db.execute(
            select(TechnicalEvaluationModel).where(
                TechnicalEvaluationModel.team_id == team_id
            )
        ).scalar_one_or_none()


class PresentationEvaluationRepository(
    BaseRepository[PresentationEvaluationModel]
):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PresentationEvaluationModel)

    def get_by_team(
        self, team_id: str
    ) -> PresentationEvaluationModel | None:
        return self.db.execute(
            select(PresentationEvaluationModel).where(
                PresentationEvaluationModel.team_id == team_id
            )
        ).scalar_one_or_none()

    def get_ranked(self) -> list[PresentationEvaluationModel]:
        return list(
            self.db.execute(
                select(PresentationEvaluationModel).order_by(
                    PresentationEvaluationModel.rank
                )
            )
            .scalars()
            .all()
        )
