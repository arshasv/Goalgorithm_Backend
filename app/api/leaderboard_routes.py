from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_current_user
from app.database.session import get_db
from app.models.leaderboard import LeaderboardModel
from app.models.leaderboard_visibility import LeaderboardVisibilityModel
from app.models.team import TeamModel
from app.models.user import UserModel
from app.models.enums import UserRole
from app.services.scoring_service import ScoringService

router = APIRouter(tags=["leaderboard"])


@router.post("/leaderboard/calculate")
def generate_leaderboard(
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    service = ScoringService(db)
    return service.compute_and_save_leaderboard(None)


@router.get("/leaderboard")
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    teams = db.query(TeamModel).all()
    team_by_uuid = {str(t.id): t for t in teams}
    team_by_letter = {t.team_id: t for t in teams}
    entries = db.query(LeaderboardModel).all()
    entries_by_team = {str(e.team_id): e for e in entries}

    result = []
    # Assign ranks to all teams. If not calculated, rank is end of the list.
    for team in teams:
        e = entries_by_team.get(str(team.id))
        if e:
            result.append({
                "id": str(e.id),
                "team_id": str(e.team_id),
                "team_code": team.team_id,
                "team_name": team.name,
                "rank": e.rank,
                "phase1_score": e.phase1_score,
                "technical_score": e.technical_score,
                "presentation_score": e.presentation_score,
                "final_score": e.final_score,
                "is_final": e.is_final,
                "generated_at": e.generated_at.isoformat(),
            })
        else:
            result.append({
                "id": f"dummy-{team.id}",
                "team_id": str(team.id),
                "team_code": team.team_id,
                "team_name": team.name,
                "rank": 999,
                "phase1_score": 0.0,
                "technical_score": 0.0,
                "presentation_score": 0.0,
                "final_score": 0.0,
                "is_final": False,
                "generated_at": None,
            })
    
    result.sort(key=lambda x: (-x["final_score"], x["team_name"]))
    # Recalculate rank based on sort just to be clean for uncalculated teams
    for i, res in enumerate(result):
        if res["rank"] == 999 or res["rank"] == 0:
            res["rank"] = i + 1

    if current_user.role == UserRole.TEAM_LEADER:
        visibility = db.query(LeaderboardVisibilityModel).first()

        show_all = (
            visibility.show_all_teams_leaderboard if visibility else True
        )

        if not show_all:
            team = db.query(TeamModel).filter(
                TeamModel.user_id == current_user.id
            ).first()
            if not team:
                return []
            result = [r for r in result if r["team_id"] == str(team.id)]

        if visibility:
            always_include = {"id", "team_id", "is_final", "generated_at"}
            show_phase = visibility.show_phase_scores

            phase_keys = set()
            if show_phase and visibility.show_phase_1_score:
                phase_keys.add("phase1_score")
            if show_phase and visibility.show_technical_score:
                phase_keys.add("technical_score")
            if show_phase and visibility.show_presentation_score:
                phase_keys.add("presentation_score")

            filtered = []
            for entry in result:
                f_entry = {}
                for key, value in entry.items():
                    if key in always_include:
                        f_entry[key] = value
                    elif key == "rank" and visibility.show_rank:
                        f_entry[key] = value
                    elif key in ("team_code", "team_name") and visibility.show_team_name:
                        f_entry[key] = value
                    elif key == "final_score" and visibility.show_final_score:
                        f_entry[key] = value
                    elif key in phase_keys:
                        f_entry[key] = value
                filtered.append(f_entry)
            result = filtered

    return result
