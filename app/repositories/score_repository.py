import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.score import CumulativePhaseScoreModel, ScoreModel
from app.repositories.base_repository import BaseRepository


class ScoreRepository(BaseRepository[ScoreModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ScoreModel)

    def get_by_team_and_match(
        self, team_id: str | uuid.UUID, match_id: str | uuid.UUID
    ) -> ScoreModel | None:
        import uuid
        if isinstance(team_id, str):
            team_id = uuid.UUID(team_id)
        if isinstance(match_id, str):
            match_id = uuid.UUID(match_id)
        return self.db.execute(
            select(ScoreModel).where(
                ScoreModel.team_id == team_id,
                ScoreModel.match_id == match_id,
            )
        ).scalar_one_or_none()

    def get_by_match(self, match_id: str | uuid.UUID) -> list[ScoreModel]:
        import uuid
        if isinstance(match_id, str):
            match_id = uuid.UUID(match_id)
        return list(
            self.db.execute(
                select(ScoreModel).where(ScoreModel.match_id == match_id)
            )
            .scalars()
            .all()
        )

    def get_by_team(self, team_id: str | uuid.UUID) -> list[ScoreModel]:
        import uuid
        if isinstance(team_id, str):
            team_id = uuid.UUID(team_id)
        return list(
            self.db.execute(
                select(ScoreModel).where(ScoreModel.team_id == team_id)
            )
            .scalars()
            .all()
        )

    def get_team_scores_for_phase(
        self, team_id: str | uuid.UUID
    ) -> list[ScoreModel]:
        import uuid
        if isinstance(team_id, str):
            team_id = uuid.UUID(team_id)
        return list(
            self.db.execute(
                select(ScoreModel)
                .where(ScoreModel.team_id == team_id)
                .where(ScoreModel.earned_points.isnot(None))
            )
            .scalars()
            .all()
        )


class CumulativePhaseScoreRepository(BaseRepository[CumulativePhaseScoreModel]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CumulativePhaseScoreModel)

    def get_by_team(
        self, team_id: str | uuid.UUID
    ) -> CumulativePhaseScoreModel | None:
        import uuid
        if isinstance(team_id, str):
            team_id = uuid.UUID(team_id)
        return self.db.execute(
            select(CumulativePhaseScoreModel).where(
                CumulativePhaseScoreModel.team_id == team_id
            )
        ).scalar_one_or_none()
