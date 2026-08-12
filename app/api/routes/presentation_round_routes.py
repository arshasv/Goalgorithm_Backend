from fastapi import APIRouter, Depends
from typing import List
from app.schemas.presentation_round_schema import PresentationRoundCreate, PresentationRoundResponse
from app.services.presentation_round_service import PresentationRoundService
from app.api.deps import get_current_organizer
from sqlalchemy.orm import Session
from app.database.session import get_db

router = APIRouter(prefix="/presentation-rounds", tags=["presentation-rounds"])

@router.get("", response_model=List[PresentationRoundResponse])
def get_presentation_rounds(
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer)
):
    """Get all presentation rounds."""
    service = PresentationRoundService(db)
    return service.get_all_rounds()

@router.post("", response_model=PresentationRoundResponse)
def create_presentation_round(
    payload: PresentationRoundCreate,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer)
):
    """Create a new presentation round."""
    service = PresentationRoundService(db)
    return service.create_round(payload)
