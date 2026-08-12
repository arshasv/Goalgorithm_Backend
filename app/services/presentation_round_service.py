from typing import List
from sqlalchemy.orm import Session
from app.models.presentation_round import PresentationRoundModel
from app.schemas.presentation_round_schema import PresentationRoundCreate
from fastapi import HTTPException

class PresentationRoundService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_rounds(self) -> List[PresentationRoundModel]:
        return self.db.query(PresentationRoundModel).order_by(PresentationRoundModel.created_at).all()

    def create_round(self, payload: PresentationRoundCreate) -> PresentationRoundModel:
        existing = self.db.query(PresentationRoundModel).filter(PresentationRoundModel.name == payload.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Presentation round with this name already exists")
        round = PresentationRoundModel(name=payload.name)
        self.db.add(round)
        self.db.commit()
        self.db.refresh(round)
        return round
