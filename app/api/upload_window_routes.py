from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_current_team_leader
from app.database.session import get_db
from app.models.upload_window import UploadWindowModel
from app.models.user import UserModel
from app.schemas.upload_window_schema import UploadWindowResponse, UploadWindowUpdate

router = APIRouter(prefix="/upload-window", tags=["upload-window"])

def get_or_create_window(db: Session) -> UploadWindowModel:
    window = db.query(UploadWindowModel).first()
    if not window:
        window = UploadWindowModel(is_enabled=False)
        db.add(window)
        db.commit()
        db.refresh(window)
    return window

@router.get("", response_model=UploadWindowResponse)
def get_upload_window(db: Session = Depends(get_db)):
    """Both organizers and team leaders can view the current window."""
    return get_or_create_window(db)

@router.put("", response_model=UploadWindowResponse)
def update_upload_window(
    update_data: UploadWindowUpdate,
    _organizer: UserModel = Depends(get_current_organizer),
    db: Session = Depends(get_db),
):
    """Only organizers can update the window."""
    window = get_or_create_window(db)
    window.is_enabled = update_data.is_enabled
    window.start_time = update_data.start_time
    window.end_time = update_data.end_time
    db.commit()
    db.refresh(window)
    return window
