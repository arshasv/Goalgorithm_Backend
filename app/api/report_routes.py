from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_organizer
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/team-breakdown", dependencies=[Depends(get_current_organizer)])
def get_team_breakdown(db: Session = Depends(get_db)):
    service = ReportService(db)
    return service.get_team_breakdown()

@router.get("/multiplier-impact", dependencies=[Depends(get_current_organizer)])
def get_multiplier_impact(db: Session = Depends(get_db)):
    service = ReportService(db)
    return service.get_multiplier_impact()

@router.get("/rank-analysis", dependencies=[Depends(get_current_organizer)])
def get_rank_analysis(db: Session = Depends(get_db)):
    service = ReportService(db)
    return service.get_rank_analysis()

@router.get("/phase-contribution", dependencies=[Depends(get_current_organizer)])
def get_phase_contribution(db: Session = Depends(get_db)):
    service = ReportService(db)
    return service.get_phase_contribution()
