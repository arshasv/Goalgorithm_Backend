from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.judge import JudgeModel
from app.api.deps import get_current_organizer
from pydantic import BaseModel

router = APIRouter(prefix="/judges", tags=["judges"])

class JudgeCreate(BaseModel):
    name: str
    employee_id: str

@router.get("")
def list_judges(db: Session = Depends(get_db), _organizer: object = Depends(get_current_organizer)):
    judges = db.query(JudgeModel).all()
    return [{"id": str(j.id), "name": j.name, "employee_id": j.employee_id} for j in judges]

@router.post("")
def create_judge(payload: JudgeCreate, db: Session = Depends(get_db), _organizer: object = Depends(get_current_organizer)):
    existing = db.query(JudgeModel).filter(JudgeModel.employee_id == payload.employee_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Judge with this Employee ID already exists")
    judge = JudgeModel(name=payload.name, employee_id=payload.employee_id)
    db.add(judge)
    db.commit()
    db.refresh(judge)
    return {"id": str(judge.id), "name": judge.name, "employee_id": judge.employee_id}

@router.delete("/{judge_id}")
def delete_judge(judge_id: str, db: Session = Depends(get_db), _organizer: object = Depends(get_current_organizer)):
    judge = db.query(JudgeModel).filter(JudgeModel.id == judge_id).first()
    if not judge:
        raise HTTPException(status_code=404, detail="Judge not found")
    db.delete(judge)
    db.commit()
    return {"status": "deleted"}
