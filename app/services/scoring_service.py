import uuid
from sqlalchemy.orm import Session

from app.models.score import ScoreModel
from app.models.scoring_config import ScoringConfigModel
from app.repositories.score_repository import (
    CumulativePhaseScoreRepository,
    ScoreRepository,
)
from app.scoring_engine.base_score.base_score_calculator import calculate_base_score
from app.scoring_engine.technical_evaluation.technical_score import (
    calculate_technical_score,
)
from app.scoring_engine.presentation_evaluation.presentation_score import (
    PHASE3_FIXED_DENOMINATOR,
    PHASE3_MAX_MARKS,
    calculate_presentation_scores,
)
from app.services.leaderboard_service import calculate_leaderboard


def _load_active_config(db: Session) -> tuple[dict | None, str | None]:
    config_record = db.query(ScoringConfigModel).filter(
        ScoringConfigModel.is_active.is_(True)
    ).first()
    if not config_record:
        return None, None
    return config_record.to_dict(), str(config_record.id)


class ScoringService:
    def __init__(self, db: Session):
        self.db = db
        self.score_repo = ScoreRepository(db)
        self.cumulative_repo = CumulativePhaseScoreRepository(db)

    def _resolve_team_uuid(self, team_id: str | uuid.UUID) -> uuid.UUID:
        import uuid
        if isinstance(team_id, uuid.UUID):
            return team_id
        # Try parsing as UUID
        try:
            return uuid.UUID(team_id)
        except ValueError:
            pass
        
        # If it's not a UUID, let's lookup by TeamModel
        from app.models.team import TeamModel
        clean_id = str(team_id).strip()
        if clean_id.lower().startswith("team "):
            clean_id = clean_id[5:].strip()
            
        # Try to find by TeamModel.team_id (e.g., 'A', 'B')
        team = self.db.query(TeamModel).filter(TeamModel.team_id == clean_id).first()
        if team:
            return team.id
            
        # Try to find by name or normalized name
        from app.utils.team_name_utils import normalize_team_name
        norm_name = normalize_team_name(str(team_id))
        team = self.db.query(TeamModel).filter(TeamModel.name_normalized == norm_name).first()
        if team:
            return team.id
            
        # Try fuzzy match by name
        team = self.db.query(TeamModel).filter(TeamModel.name.ilike(f"%{clean_id}%")).first()
        if team:
            return team.id
            
        # Fallback to converting as UUID (it will fail/raise)
        return uuid.UUID(str(team_id))

    def _resolve_match_uuid(self, match_id: str | uuid.UUID) -> uuid.UUID:
        import uuid
        if isinstance(match_id, uuid.UUID):
            return match_id
        try:
            return uuid.UUID(match_id)
        except ValueError:
            pass
            
        # Look up match by match_number or name
        from app.models.match import MatchModel
        clean_id = str(match_id).strip()
        
        # If it's like "M1" or "M01", extract number
        import re
        m = re.match(r'^M?(\d+)$', clean_id, re.IGNORECASE)
        if m:
            num = int(m.group(1))
            match_obj = self.db.query(MatchModel).filter(MatchModel.match_number == num).first()
            if match_obj:
                return match_obj.id
                
        # Try querying by ID string directly or fallback
        return uuid.UUID(str(match_id))

    def calculate_and_save_match_score(
        self, prediction: dict, actual_result: dict, actual_probabilities: dict | None = None
    ) -> dict:
        config_dict, config_id = _load_active_config(self.db)
        result = calculate_base_score(prediction, actual_result, actual_probabilities, config_dict)

        import uuid
        from sqlalchemy.dialects.postgresql import insert

        team_uuid = self._resolve_team_uuid(prediction["team_id"])
        match_uuid = self._resolve_match_uuid(prediction["match_id"])

        stmt = insert(ScoreModel).values(
            team_id=team_uuid,
            match_id=match_uuid,
            winner_points=result["breakdown"].get("winner_score", 0.0),
            scoreline_points=result["breakdown"].get("scoreline_score", 0.0),
            probability_points=result["breakdown"].get("probability_score", 0.0),
            player_points=result["breakdown"].get("player_score", 0.0),
            total_goals_points=result["breakdown"].get("total_goals_score", 0.0),
            btts_points=result["breakdown"].get("btts_score", 0.0),
            first_team_to_score_points=result["breakdown"].get("first_team_to_score_score", 0.0),
            clean_sheet_points=result["breakdown"].get("clean_sheet_score", 0.0),
            base_score=result["base_score"],
            config_id=config_id,
        )

        update_dict = {
            c.name: c for c in stmt.excluded if c.name not in ["id", "team_id", "match_id", "computed_at"]
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=["team_id", "match_id"],
            set_=update_dict
        ).returning(ScoreModel.id)

        self.db.execute(stmt)
        self.db.commit()

        return result

    def calculate_and_save_technical_score(self, evaluation: dict) -> dict:
        config_dict, config_id = _load_active_config(self.db)
        result = calculate_technical_score(evaluation, config_dict)

        from app.models.evaluation import TechnicalEvaluationModel

        team_id = self._resolve_team_uuid(evaluation["team_id"])
        existing = self.db.query(TechnicalEvaluationModel).filter(
            TechnicalEvaluationModel.team_id == team_id
        ).first()
        if existing:
            for key, value in {
                "code_quality": evaluation.get("code_quality"),
                "backend_quality": evaluation.get("backend_quality"),
                "teamwork": evaluation.get("teamwork"),
                "ai_explanation": evaluation.get("ai_explanation"),
                "total_score": result["technical_score"],
            }.items():
                setattr(existing, key, value)
            self.db.commit()
        else:
            tech_eval = TechnicalEvaluationModel(
                team_id=team_id,
                code_quality=evaluation.get("code_quality"),
                backend_quality=evaluation.get("backend_quality"),
                teamwork=evaluation.get("teamwork"),
                ai_explanation=evaluation.get("ai_explanation"),
                total_score=result["technical_score"],
            )
            self.db.add(tech_eval)
            self.db.commit()

        return result

    def calculate_and_save_presentation_scores(
        self, evaluations: list[dict], round_id: str | None = None
    ) -> list[dict]:
        config, _ = _load_active_config(self.db)
        result = calculate_presentation_scores(evaluations, config)

        from app.models.evaluation import PresentationEvaluationModel

        for ev in result:
            try:
                team_id = self._resolve_team_uuid(ev["team_id"])
            except ValueError:
                continue
            query = self.db.query(PresentationEvaluationModel).filter(
                PresentationEvaluationModel.team_id == team_id
            )
            if round_id:
                query = query.filter(PresentationEvaluationModel.round_id == round_id)
            else:
                # To handle legacy items without round_id, fallback to picking the first one
                pass
                
            existing = query.first()

            if existing:
                existing.presentation_score = ev["presentation_score"]
                existing.raw_total = ev["raw_total"]
                existing.rank = ev["rank"]
                existing.grade = ev["grade"]
                existing.multiplier = ev["multiplier"]
                existing.judge_count = ev["judge_count"]
                existing.judge_scores = ev["judge_scores"]
                existing.presentation_criteria_config = ev["presentation_criteria_config"]
                existing.max_marks = ev["max_marks"]
                existing.round_id = round_id
                self.db.commit()
            else:
                pres_eval = PresentationEvaluationModel(
                    team_id=team_id,
                    raw_total=ev["raw_total"],
                    presentation_score=ev["presentation_score"],
                    rank=ev["rank"],
                    grade=ev["grade"],
                    multiplier=ev["multiplier"],
                    judge_count=ev["judge_count"],
                    judge_scores=ev["judge_scores"],
                    presentation_criteria_config=ev["presentation_criteria_config"],
                    max_marks=ev["max_marks"],
                    round_id=round_id
                )
                self.db.add(pres_eval)
                self.db.commit()

        return result


    def compute_and_save_leaderboard(
        self, scores_input: list[dict] = None
    ) -> list[dict]:
        import uuid
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=== compute_and_save_leaderboard START ===")

        from app.models.team import TeamModel
        from app.models.evaluation import TechnicalEvaluationModel, PresentationEvaluationModel
        
        teams = self.db.query(TeamModel).all()
        all_scores = self.db.query(ScoreModel).all()
        tech_evals = self.db.query(TechnicalEvaluationModel).all()
        pres_evals = self.db.query(PresentationEvaluationModel).all()

        logger.info("Teams=%s, total scores=%s, tech evals=%s, pres evals=%s",
                     len(teams), len(all_scores), len(tech_evals), len(pres_evals))
        
        config_dict, _ = _load_active_config(self.db)
        phase1_max = config_dict.get("phase1_max_marks", 60) if config_dict else 60
        
        team_earned_points = {str(t.id): 0.0 for t in teams}
        for s in all_scores:
            if s.earned_points is not None:
                tid = str(s.team_id)
                if tid in team_earned_points:
                    team_earned_points[tid] += s.earned_points
                
        unique_match_ids = set(str(s.match_id) for s in all_scores)
        total_matches = len(unique_match_ids)
        max_earned_per_match = 75  # 25 base * 3× multiplier
        total_possible = total_matches * max_earned_per_match
        logger.info("Total matches evaluated: %s, total possible points: %s", total_matches, total_possible)
        
        tech_map = {str(e.team_id): e.total_score for e in tech_evals}
        # Aggregate presentation rounds (multiple rounds per team)
        team_pres_totals = {}
        unique_rounds = set()
        has_null_round = False
        
        for e in pres_evals:
            if e.raw_total is not None:
                if e.round_id is not None:
                    unique_rounds.add(e.round_id)
                else:
                    has_null_round = True
                    
                tid = str(e.team_id)
                weighted = e.raw_total * (e.multiplier or 1)
                team_pres_totals[tid] = team_pres_totals.get(tid, 0.0) + weighted
                
        round_count = len(unique_rounds) + (1 if has_null_round else 0)
        presentation_denominator = max(round_count * 150, 150)
                
        # Normalize to max 20 using dynamic denominator
        pres_map = {
            tid: round((total / presentation_denominator) * PHASE3_MAX_MARKS, 2)
            for tid, total in team_pres_totals.items()
        }
        
        computed_input = []
        for t in teams:
            tid = str(t.id)
            earned = team_earned_points[tid]
            if total_possible > 0:
                p1 = (earned / total_possible) * phase1_max
            else:
                p1 = 0.0
            p1 = min(p1, phase1_max)
                
            computed_input.append({
                "team_id": tid,
                "phase1_score": round(p1, 2),
                "technical_score": tech_map.get(tid, 0.0),
                "presentation_score": pres_map.get(tid, 0.0)
            })

        ranked = calculate_leaderboard(computed_input)

        from app.models.leaderboard import LeaderboardModel
        from app.models.score import CumulativePhaseScoreModel

        for entry in ranked:
            team_id_str = entry["team_id"]
            team_id_uuid = uuid.UUID(team_id_str)
            # Query with explicit UUID object to avoid type coercion issues
            existing = self.db.query(LeaderboardModel).filter(
                LeaderboardModel.team_id == team_id_uuid
            ).first()

            scores = entry.get("scores", {})

            if existing:
                existing.rank = entry["rank"]
                existing.phase1_score = scores.get("ai_accuracy")
                existing.technical_score = scores.get("technical")
                existing.presentation_score = scores.get("presentation")
                existing.final_score = entry["final_score"]
                existing.is_final = True
            else:
                leaderboard_entry = LeaderboardModel(
                    team_id=team_id_uuid,
                    rank=entry["rank"],
                    phase1_score=scores.get("ai_accuracy"),
                    technical_score=scores.get("technical"),
                    presentation_score=scores.get("presentation"),
                    final_score=entry["final_score"],
                    is_final=True,
                )
                self.db.add(leaderboard_entry)
                
            # Update cumulative phase scores to match leaderboard recalculations
            cum_existing = self.db.query(CumulativePhaseScoreModel).filter(
                CumulativePhaseScoreModel.team_id == team_id_uuid
            ).first()
            
            matches_played = len([s for s in all_scores if str(s.team_id) == team_id_str])
            if cum_existing:
                cum_existing.phase1_score = scores.get("ai_accuracy")
                cum_existing.technical_score = scores.get("technical")
                cum_existing.presentation_score = scores.get("presentation")
                cum_existing.total_earned_points = team_earned_points.get(team_id_str, 0.0)
                cum_existing.matches_played = matches_played
            else:
                cum_entry = CumulativePhaseScoreModel(
                    team_id=team_id_uuid,
                    phase1_score=scores.get("ai_accuracy"),
                    technical_score=scores.get("technical"),
                    presentation_score=scores.get("presentation"),
                    total_earned_points=team_earned_points.get(team_id_str, 0.0),
                    matches_played=matches_played
                )
                self.db.add(cum_entry)
                
        self.db.commit()

        logger.info("=== compute_and_save_leaderboard END ===")
        return ranked
