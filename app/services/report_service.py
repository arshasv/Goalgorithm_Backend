from sqlalchemy.orm import Session
from app.models.team import TeamModel
from app.models.score import ScoreModel
from app.models.evaluation import TechnicalEvaluationModel, PresentationEvaluationModel
from app.models.leaderboard import LeaderboardModel
from app.models.presentation_round import PresentationRoundModel
from app.services.scoring_service import _load_active_config
from app.scoring_engine.presentation_evaluation.presentation_score import PHASE3_MAX_MARKS

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def get_team_breakdown(self):
        teams = self.db.query(TeamModel).all()
        all_scores = self.db.query(ScoreModel).all()
        tech_evals = self.db.query(TechnicalEvaluationModel).all()
        pres_evals = self.db.query(PresentationEvaluationModel).all()
        leaderboards = self.db.query(LeaderboardModel).all()
        
        config_dict, _ = _load_active_config(self.db)
        phase1_max = config_dict.get("phase1_max_marks", 60) if config_dict else 60
        tech_max = 20 # typically max out of 20
        
        # calculate max base score for phase 1 normalization
        team_base_scores = {str(t.id): 0.0 for t in teams}
        for s in all_scores:
            if s.base_score is not None:
                tid = str(s.team_id)
                if tid in team_base_scores:
                    team_base_scores[tid] += s.base_score
                
        max_base_score = max(team_base_scores.values()) if team_base_scores else 0.0

        tech_map = {str(e.team_id): e for e in tech_evals}
        leaderboard_map = {str(l.team_id): l for l in leaderboards}

        # Presentation normalization logic
        team_pres_rounds = {}
        unique_rounds = set()
        has_null_round = False
        
        for e in pres_evals:
            if e.raw_total is not None:
                if e.round_id is not None:
                    unique_rounds.add(e.round_id)
                else:
                    has_null_round = True
                
                tid = str(e.team_id)
                if tid not in team_pres_rounds:
                    team_pres_rounds[tid] = []
                team_pres_rounds[tid].append(e)

        round_count = len(unique_rounds) + (1 if has_null_round else 0)
        presentation_denominator = max(round_count * 150, 150)
        
        # Fetch round details to map names
        rounds = self.db.query(PresentationRoundModel).all()
        round_map = {str(r.id): r.name for r in rounds}
        
        breakdown = []
        for t in teams:
            tid = str(t.id)
            
            # Phase 1
            raw_p1 = team_base_scores[tid]
            if max_base_score > 0:
                p1_normalized = (raw_p1 / max_base_score) * phase1_max
            else:
                p1_normalized = 0.0
            
            # Phase 2
            tech_eval = tech_map.get(tid)
            raw_tech = tech_eval.total_score if tech_eval else 0.0
            tech_normalized = tech_eval.total_score if tech_eval else 0.0 # Assumed normalized matches raw up to 20
            
            # Phase 3
            pres_round_data = []
            total_pres_weighted = 0.0
            team_rounds = team_pres_rounds.get(tid, [])
            for e in team_rounds:
                weighted = e.raw_total * (e.multiplier or 1)
                total_pres_weighted += weighted
                round_name = round_map.get(str(e.round_id), "Default Round") if e.round_id else "Default Round"
                pres_round_data.append({
                    "round_name": round_name,
                    "raw_score": e.raw_total,
                    "grade": e.grade,
                    "multiplier": e.multiplier,
                    "weighted_score": weighted,
                    "max_weighted": 150
                })
                
            pres_normalized = round((total_pres_weighted / presentation_denominator) * PHASE3_MAX_MARKS, 2)
            
            # Final
            lb = leaderboard_map.get(tid)
            final_score = lb.final_score if lb else round(p1_normalized + tech_normalized + pres_normalized, 2)
            
            breakdown.append({
                "team_id": tid,
                "team_name": t.name,
                "phase1": {
                    "raw_score": raw_p1,
                    "max_raw": max_base_score,
                    "normalized_score": round(p1_normalized, 2),
                    "max_normalized": phase1_max
                },
                "technical": {
                    "raw_score": raw_tech,
                    "max_raw": 20,
                    "normalized_score": raw_tech
                },
                "presentation": {
                    "rounds": pres_round_data,
                    "total_weighted": total_pres_weighted,
                    "total_possible_weighted": presentation_denominator,
                    "normalized_score": pres_normalized
                },
                "final_score": final_score
            })
            
        return breakdown

    def get_multiplier_impact(self):
        teams = self.db.query(TeamModel).all()
        pres_evals = self.db.query(PresentationEvaluationModel).all()
        team_map = {str(t.id): t.name for t in teams}
        
        impact = []
        for e in pres_evals:
            if e.raw_total is not None:
                weighted = e.raw_total * (e.multiplier or 1)
                gain = weighted - e.raw_total
                impact.append({
                    "team": team_map.get(str(e.team_id), "Unknown"),
                    "raw_score": e.raw_total,
                    "grade": e.grade,
                    "multiplier": e.multiplier,
                    "weighted_score": weighted,
                    "gain": gain
                })
        return impact

    def get_rank_analysis(self):
        # We define ranking before processing as ranking without any multipliers
        # Just phase1 normalized + tech raw + pres raw (normalized without multipliers)
        # However, for simplicity and typical analytics, we can use base raw scores.
        # But wait, the prompt says "We define ranking before processing vs ranking after final leaderboard."
        # And provides an example in the prompt earlier "Raw Presentation Rank vs Final Overall Rank".
        
        teams = self.db.query(TeamModel).all()
        pres_evals = self.db.query(PresentationEvaluationModel).all()
        leaderboards = self.db.query(LeaderboardModel).all()
        
        team_map = {str(t.id): t.name for t in teams}
        lb_map = {str(l.team_id): l for l in leaderboards}
        
        # Calculate raw presentation sum per team to get raw presentation rank
        pres_raw_sums = {}
        for e in pres_evals:
            if e.raw_total is not None:
                tid = str(e.team_id)
                pres_raw_sums[tid] = pres_raw_sums.get(tid, 0.0) + e.raw_total
                
        # rank them by raw_total
        sorted_raw_pres = sorted([{'tid': k, 'val': v} for k, v in pres_raw_sums.items()], key=lambda x: x['val'], reverse=True)
        raw_pres_ranks = {}
        for i, item in enumerate(sorted_raw_pres):
            raw_pres_ranks[item['tid']] = i + 1
            
        # rank analysis result
        results = []
        for t in teams:
            tid = str(t.id)
            final_lb = lb_map.get(tid)
            if not final_lb:
                continue
                
            raw_rank = raw_pres_ranks.get(tid, len(teams))
            final_rank = final_lb.rank
            
            results.append({
                "team": team_map.get(tid, "Unknown"),
                "raw_rank": raw_rank,
                "final_rank": final_rank,
                "movement": raw_rank - final_rank
            })
            
        return results

    def get_phase_contribution(self):
        teams = self.db.query(TeamModel).all()
        leaderboards = self.db.query(LeaderboardModel).all()
        team_map = {str(t.id): t.name for t in teams}
        
        results = []
        for lb in leaderboards:
            results.append({
                "team": team_map.get(str(lb.team_id), "Unknown"),
                "prediction_contribution": lb.phase1_score or 0.0,
                "technical_contribution": lb.technical_score or 0.0,
                "presentation_contribution": lb.presentation_score or 0.0,
                "final_score": lb.final_score or 0.0
            })
            
        return results
