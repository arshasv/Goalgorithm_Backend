import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction import PlayerPredictionModel, PredictionModel
from app.repositories.base_repository import BaseRepository


class PredictionRepository(BaseRepository[PredictionModel]):

    def __init__(self, db: Session) -> None:
        super().__init__(db, PredictionModel)


    def get_by_team_and_match(
        self,
        team_id: str | uuid.UUID,
        match_id: str | uuid.UUID
    ) -> PredictionModel | None:
        t_id = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
        m_id = uuid.UUID(match_id) if isinstance(match_id, str) else match_id
        res = self.db.execute(
            select(PredictionModel).where(
                PredictionModel.team_id == t_id,
                PredictionModel.match_id == m_id
            )
        ).scalar_one_or_none()
        return res

    def get_by_match(
        self,
        match_id: str | uuid.UUID
    ) -> list[PredictionModel]:
        m_id = uuid.UUID(match_id) if isinstance(match_id, str) else match_id
        return list(
            self.db.execute(
                select(PredictionModel).where(
                    PredictionModel.match_id == m_id
                )
            )
            .scalars()
            .all()
        )

    def get_by_team(
        self,
        team_id: str | uuid.UUID
    ) -> list[PredictionModel]:
        t_id = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
        return list(
            self.db.execute(
                select(PredictionModel).where(
                    PredictionModel.team_id == t_id
                )
            )
            .scalars()
            .all()
        )



    def get_by_idempotency_key(
        self,
        key: str
    ) -> PredictionModel | None:

        return self.db.execute(

            select(PredictionModel).where(

                PredictionModel.idempotency_key == key

            )

        ).scalar_one_or_none()



    def add_player_predictions(
        self,
        prediction: PredictionModel,
        player_data_list: list[dict]
    ) -> list[PlayerPredictionModel]:


        players = []


        for data in player_data_list:

            player = PlayerPredictionModel(

                prediction_id=prediction.id,

                **data

            )

            self.db.add(player)

            players.append(player)


        self.db.commit()


        for p in players:

            self.db.refresh(p)


        return players



    def get_player_predictions(
        self,
        prediction_id: uuid.UUID
    ) -> list[PlayerPredictionModel]:


        return list(

            self.db.execute(

                select(PlayerPredictionModel).where(

                    PlayerPredictionModel.prediction_id == prediction_id

                )

            )
            .scalars()
            .all()

        )