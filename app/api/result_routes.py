from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_current_user
from app.database.session import get_db
from app.models.user import UserModel
from app.schemas import ActualResultSubmission
from app.services.result_service import ResultService

router = APIRouter(tags=["actual-results"])


@router.post("/actual-results")
def submit_actual_result(
    payload: ActualResultSubmission,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    service = ResultService(db)
    
    return service.save_actual_result(payload.model_dump())


@router.get("/actual-results/{match_id}")
def get_actual_result(
    match_id: str,
    db: Session = Depends(get_db),
    _user: UserModel = Depends(get_current_user),
):
    service = ResultService(db)
    result = service.get_by_match(match_id)
    if not result:
        raise HTTPException(status_code=404, detail="No actual result found for this match")
    return result

