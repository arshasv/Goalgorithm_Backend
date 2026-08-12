from datetime import date
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import UserModel
from app.repositories.score_repository import ScoreRepository
from app.repositories.match_repository import MatchRepository, ActualResultRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.leaderboard_repository import (
    TechnicalEvaluationRepository,
    PresentationEvaluationRepository,
    JudgeRepository,
    PresentationScoreRepository,
)


class ScoresService:
    def __init__(
        self,
        score_repo: ScoreRepository,
        match_repo: MatchRepository,
        team_repo: TeamRepository,
        actual_repo: ActualResultRepository,
        pred_repo: PredictionRepository,
        tech_repo: TechnicalEvaluationRepository,
        pres_repo: PresentationEvaluationRepository,
        judge_repo: JudgeRepository,
        pres_score_repo: PresentationScoreRepository,
    ) -> None:
        self.score_repo = score_repo
        self.match_repo = match_repo
        self.team_repo = team_repo
        self.actual_repo = actual_repo
        self.pred_repo = pred_repo
        self.tech_repo = tech_repo
        self.pres_repo = pres_repo
        self.judge_repo = judge_repo
        self.pres_score_repo = pres_score_repo

    def _get_team_name_map(self) -> dict[str, str]:
        """Build a name lookup keyed by both UUID str and team letter code."""
        result = {}
        for t in self.team_repo.get_all():
            uuid_key = str(t.id)
            result[uuid_key] = t.name
            # Also index by team letter code (e.g. 'A', 'B') so lookups
            # succeed regardless of which format is stored in evaluation rows.
            if t.team_id:
                result[str(t.team_id)] = t.name
        return result

    def _get_team_id_map(self) -> dict[str, str]:
        """Build a team-code lookup keyed by both UUID str and team letter code."""
        result = {}
        for t in self.team_repo.get_all():
            uuid_key = str(t.id)
            result[uuid_key] = t.team_id
            if t.team_id:
                result[str(t.team_id)] = t.team_id
        return result

    def _get_team_id_for_user(self, user: UserModel) -> str | None:
        user_teams = self.team_repo.get_by_user_id(user.id)
        return str(user_teams[0].id) if user_teams else None

    def get_daily_scores(self, user: UserModel) -> list[dict]:
        scores = [s for s in self.score_repo.get_all() if s.base_score is not None]
        matches = {str(m.id): m for m in self.match_repo.get_all()}
        team_names = self._get_team_name_map()
        team_codes = self._get_team_id_map()

        is_organizer = user.role == UserRole.ORGANIZER
        user_team_id = self._get_team_id_for_user(user) if not is_organizer else None

        daily: dict[date, dict[str, dict]] = {}
        for s in scores:
            match = matches.get(str(s.match_id))
            if not match:
                continue
            if not is_organizer and str(s.team_id) != user_team_id:
                continue

            d = match.scheduled_at.date()
            if d not in daily:
                daily[d] = {}
            team_name = team_names.get(str(s.team_id), "Unknown Team")
            team_code = team_codes.get(str(s.team_id), "")
            if team_name not in daily[d]:
                daily[d][team_name] = {"total_score": 0, "team_code": team_code}
            daily[d][team_name]["total_score"] += s.base_score or 0

        result = []
        for d in sorted(daily.keys(), reverse=True):
            entries = [
                {"team_name": name, "team_code": data["team_code"], "total_score": round(data["total_score"], 1)}
                for name, data in daily[d].items()
            ]
            entries.sort(key=lambda x: x["total_score"], reverse=True)
            for i, e in enumerate(entries):
                e["rank"] = i + 1
            result.append({"date": d.isoformat(), "teams": entries})

        return result

    def get_match_breakdown(self, user: UserModel) -> list[dict]:
        matches = self.match_repo.get_all_ordered()
        team_names = self._get_team_name_map()
        team_codes = self._get_team_id_map()

        is_organizer = user.role == UserRole.ORGANIZER
        user_team_id = self._get_team_id_for_user(user) if not is_organizer else None

        actuals = {str(a.match_id): a for a in self.actual_repo.get_all()}
        scores_by_match: dict[str, list] = {}
        for s in self.score_repo.get_all():
            scores_by_match.setdefault(str(s.match_id), []).append(s)

        predictions_by_key = {}
        for p in self.pred_repo.get_all():
            predictions_by_key[(str(p.team_id), str(p.match_id))] = p

        result = []
        for m in matches:
            mid = str(m.id)
            actual = actuals.get(mid)
            match_scores = scores_by_match.get(mid, [])

            teams = []
            for s in match_scores:
                if not is_organizer and str(s.team_id) != user_team_id:
                    continue

                team_name = team_names.get(str(s.team_id), "Unknown Team")
                pred = predictions_by_key.get((str(s.team_id), mid))
                prediction_detail = None
                if pred:
                    prediction_detail = {
                        "predicted_winner": pred.predicted_winner.value if pred.predicted_winner else None,
                        "predicted_home_goals": pred.predicted_home_goals,
                        "predicted_away_goals": pred.predicted_away_goals,
                        "status": pred.status.value if pred.status else None,
                    }

                teams.append({
                    "team_id": str(s.team_id),
                    "team_code": team_codes.get(str(s.team_id), ""),
                    "team_name": team_name,
                    "prediction": prediction_detail,
                    "score_breakdown": {
                        "winner_points": s.winner_points,
                        "scoreline_points": s.scoreline_points,
                        "probability_points": s.probability_points,
                        "player_points": s.player_points,
                        "total_goals_points": s.total_goals_points,
                        "btts_points": s.btts_points,
                        "first_team_to_score_points": s.first_team_to_score_points,
                        "clean_sheet_points": s.clean_sheet_points,
                        "base_score": s.base_score,
                        "earned_points": s.earned_points,
                        "match_rank": s.match_rank,
                        "grade": s.grade.value if s.grade else None,
                        "multiplier": s.multiplier,
                    },
                })

            actual_detail = None
            if actual:
                actual_detail = {
                    "actual_winner": actual.actual_winner.value if actual.actual_winner else None,
                    "actual_home_goals": actual.actual_home_goals,
                    "actual_away_goals": actual.actual_away_goals,
                }

            result.append({
                "match_id": mid,
                "match_number": m.match_number,
                "home_team_name": m.home_team_name,
                "away_team_name": m.away_team_name,
                "scheduled_at": m.scheduled_at.isoformat(),
                "status": m.status.value if m.status else None,
                "actual_result": actual_detail,
                "teams": teams,
            })

        return result

    def get_technical_evaluations(self) -> list[dict]:
        team_names = self._get_team_name_map()
        team_codes = self._get_team_id_map()
        evaluations = self.tech_repo.get_all()

        return [
            {
                "team_id": e.team_id,
                "team_code": team_codes.get(e.team_id, ""),
                "team_name": team_names.get(e.team_id, "Unknown Team"),
                "code_quality": e.code_quality,
                "backend_quality": e.backend_quality,
                "teamwork": e.teamwork,
                "ai_explanation": e.ai_explanation,
                "total_score": e.total_score,
                "submitted_at": e.submitted_at.isoformat() if e.submitted_at else None,
            }
            for e in evaluations
        ]

    def _resolve_judge(self, jid_raw, judges: dict):
        """Resolve a judge from the lookup map, normalizing UUID format."""
        if jid_raw is None:
            return None
        jid_str = str(jid_raw).strip()
        judge = judges.get(jid_str)
        if judge:
            return judge
        # Try stripping hyphens in case storage format differs
        jid_no_hyphens = jid_str.replace("-", "")
        for key, val in judges.items():
            if key.replace("-", "") == jid_no_hyphens:
                return val
        return None

    def get_presentation_evaluations(self, round_id: str | None = None) -> list[dict]:
        team_names = self._get_team_name_map()
        team_codes = self._get_team_id_map()

        if round_id:
            evaluations = self.pres_repo.get_by_round(round_id)
        else:
            evaluations = self.pres_repo.get_all()

        judges = {str(j.id): j for j in self.judge_repo.get_all()}

        result_evals = []
        for e in evaluations:
            db_scores = self.pres_score_repo.get_by_team(e.team_id, round_id=round_id)

            judge_scores_list = []
            if db_scores:
                for dbs in db_scores:
                    jid_str = str(dbs.judge_id)
                    judge = self._resolve_judge(jid_str, judges)

                    js_entry = {
                        "judge_id": jid_str,
                        "judge_name": judge.name if judge else "Unknown Judge",
                        "employee_id": judge.employee_id if judge else "",
                        "scores": dbs.scores,
                    }
                    if isinstance(dbs.scores, dict):
                        js_entry.update(dbs.scores)

                    judge_scores_list.append(js_entry)
            else:
                for js in (e.judge_scores or []):
                    if not isinstance(js, dict):
                        continue
                    jid_raw = js.get("judge_id")
                    judge = self._resolve_judge(jid_raw, judges) if jid_raw else None
                    jid_str = str(jid_raw) if jid_raw else ""

                    scores_data = js.get("scores", {})
                    js_entry = {
                        "judge_id": jid_str,
                        "judge_name": judge.name if judge else (js.get("judge_name") or "Unknown Judge"),
                        "employee_id": judge.employee_id if judge else (js.get("employee_id") or ""),
                        "scores": scores_data,
                    }
                    if isinstance(scores_data, dict):
                        js_entry.update(scores_data)
                    judge_scores_list.append(js_entry)

            result_evals.append({
                "team_id": e.team_id,
                "team_code": team_codes.get(e.team_id, ""),
                "team_name": team_names.get(e.team_id, "Unknown Team"),
                "ai_explanation_score": e.ai_explanation_score,
                "qa_score": e.qa_score,
                "delivery_score": e.delivery_score,
                "raw_total": e.raw_total,
                "weighted_score": (e.raw_total or 0) * (e.multiplier or 0),
                "presentation_score": e.presentation_score,
                "round_id": str(e.round_id) if getattr(e, 'round_id', None) else None,
                "rank": e.rank,
                "grade": e.grade.value if e.grade else None,
                "multiplier": e.multiplier,
                "judge_count": e.judge_count,
                "judge_scores": judge_scores_list,
                "presentation_criteria_config": e.presentation_criteria_config or [],
                "max_marks": e.max_marks,
                "submitted_at": e.submitted_at.isoformat() if e.submitted_at else None,
            })

        return result_evals
