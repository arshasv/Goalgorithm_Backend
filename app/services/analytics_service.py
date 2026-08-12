import uuid
from collections import defaultdict
from typing import List, Dict, Any, Optional

from app.repositories.analytics_repository import AnalyticsRepository
from app.models.scoring_config import ScoringConfigModel
from sqlalchemy.orm import Session


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalyticsRepository(db)

    def _team_name_map(self) -> dict[str, str]:
        teams = self.repo.get_active_teams()
        return {str(t.id): t.name for t in teams}

    def _load_criteria_config(self) -> list[dict]:
        config = self.db.query(ScoringConfigModel).filter(ScoringConfigModel.is_active == True).first()
        if config and config.presentation_criteria:
            return config.presentation_criteria
        return [
            {"name": "Problem Understanding", "max_score": 10},
            {"name": "Feature Engineering", "max_score": 15},
            {"name": "Team Work", "max_score": 10},
            {"name": "Presentation Quality", "max_score": 10},
            {"name": "Q&A", "max_score": 5},
        ]

    def get_overview(self) -> dict:
        teams = self.repo.get_active_teams()
        total_teams = len(teams)

        lb_entries = self.repo.get_all_leaderboard_entries()
        if not lb_entries:
            return {
                "total_teams": total_teams,
                "top_team": None,
                "average_scores": {
                    "phase1_average": None,
                    "technical_average": None,
                    "presentation_average": None,
                    "final_average": None,
                },
            }

        names = self._team_name_map()

        best = max(lb_entries, key=lambda e: (e.final_score or 0))
        top_team = {
            "team_name": names.get(str(best.team_id), "Unknown"),
            "final_score": best.final_score,
        }

        def _avg(attr: str) -> float | None:
            vals = [getattr(e, attr) for e in lb_entries if getattr(e, attr) is not None]
            return round(sum(vals) / len(vals), 2) if vals else None

        return {
            "total_teams": total_teams,
            "top_team": top_team,
            "average_scores": {
                "phase1_average": _avg("phase1_score"),
                "technical_average": _avg("technical_score"),
                "presentation_average": _avg("presentation_score"),
                "final_average": _avg("final_score"),
            },
        }

    def get_models_analytics(self) -> list[dict]:
        teams = self.repo.get_active_teams()
        names = self._team_name_map()

        all_scores = self.repo.get_all_calculated_scores()
        scores_by_team = defaultdict(list)
        for s in all_scores:
            scores_by_team[str(s.team_id)].append(s)

        matches = {str(m.id): m for m in self.repo.get_all_matches()}

        results = []
        for team in teams:
            tid = str(team.id)
            team_scores = scores_by_team.get(tid, [])
            if not team_scores:
                continue

            total = len(team_scores)
            correct_winners = sum(1 for s in team_scores if (s.winner_points or 0) > 0)
            total_earned = sum(s.earned_points or 0 for s in team_scores)
            avg_match = round(total_earned / total, 2) if total else None
            winner_acc = round((correct_winners / total) * 100, 1) if total else None

            ranking_trend = []
            for s in team_scores:
                m = matches.get(s.match_id)
                ranking_trend.append({
                    "match_number": m.match_number if m else 0,
                    "match_label": f"{m.home_team_name} vs {m.away_team_name}" if m else "Unknown",
                    "rank": s.match_rank,
                    "score": s.base_score,
                    "winner_score": s.winner_points or 0,
                    "scoreline_score": s.scoreline_points or 0,
                    "probability_score": s.probability_points or 0,
                    "player_score": s.player_points or 0,
                })
            ranking_trend.sort(key=lambda x: x["match_number"])

            model = self.repo.get_latest_model_for_team(team.id)
            model_obj = None
            if model:
                model_obj = {
                    "model_name": model.file_name,
                    "file_name": model.file_name,
                    "upload_date": model.uploaded_at.isoformat() if model.uploaded_at else None,
                    "is_active": model.is_active,
                }

            results.append({
                "team": names.get(tid, "Unknown"),
                "model_information": model_obj,
                "performance": {
                    "matches_predicted": total,
                    "total_ai_score": round(total_earned, 2),
                    "average_match_score": avg_match,
                    "accuracy_percentage": winner_acc,
                    "ranking_trend": ranking_trend,
                },
            })

        return results

    def get_presentation_analytics(self) -> dict:
        teams = self.repo.get_active_teams()
        names = self._team_name_map()
        fallback_criteria = self._load_criteria_config()

        evals = self.repo.get_all_presentation_evaluations()
        evals_by_team = defaultdict(list)
        for ev in evals:
            evals_by_team[str(ev.team_id)].append(ev)

        team_criteria = defaultdict(lambda: defaultdict(lambda: {"sum": 0.0, "count": 0, "max_score": 0}))

        for tid, team_evals in evals_by_team.items():
            for ev in team_evals:
                criteria_config = ev.presentation_criteria_config or fallback_criteria
                max_by_name = {c["name"]: c["max_score"] for c in criteria_config}

                judge_scores = ev.judge_scores or []
                for j_score in judge_scores:
                    if isinstance(j_score, dict) and "scores" in j_score:
                        s_dict = j_score["scores"]
                    elif isinstance(j_score, dict):
                        s_dict = j_score
                    else:
                        continue

                    for cname, cval in s_dict.items():
                        try:
                            val = float(cval)
                        except (ValueError, TypeError):
                            continue
                        tc = team_criteria[tid][cname]
                        tc["sum"] += val
                        tc["count"] += 1
                        tc["max_score"] = max(tc["max_score"], max_by_name.get(cname, 0))

        team_results = []
        for team in teams:
            tid = str(team.id)
            if tid not in team_criteria:
                continue

            criteria_list = []
            for cname, data in team_criteria[tid].items():
                avg = round(data["sum"] / data["count"], 2) if data["count"] else 0.0
                criteria_list.append({
                    "criterion": cname,
                    "avg_score": avg,
                    "max_score": data["max_score"],
                })

            if not criteria_list:
                continue

            criteria_list.sort(key=lambda x: x["criterion"])
            strongest = max(criteria_list, key=lambda x: (x["avg_score"] / x["max_score"]) if x["max_score"] else 0)
            weakest = min(criteria_list, key=lambda x: (x["avg_score"] / x["max_score"]) if x["max_score"] else float("inf"))

            def _pct(item):
                return round((item["avg_score"] / item["max_score"]) * 100, 1) if item["max_score"] else 0.0

            team_results.append({
                "team": names.get(tid, "Unknown"),
                "strongest": {
                    "criterion": strongest["criterion"],
                    "score": strongest["avg_score"],
                    "max_score": strongest["max_score"],
                    "pct": _pct(strongest),
                },
                "weakest": {
                    "criterion": weakest["criterion"],
                    "score": weakest["avg_score"],
                    "max_score": weakest["max_score"],
                    "pct": _pct(weakest),
                },
                "criteria_averages": [
                    {"criterion": c["criterion"], "avg_score": c["avg_score"], "max_score": c["max_score"]}
                    for c in criteria_list
                ],
            })

        criterion_rankings = defaultdict(list)
        for tr in team_results:
            for ca in tr["criteria_averages"]:
                criterion_rankings[ca["criterion"]].append(
                    (tr["team"], ca["avg_score"], ca["max_score"])
                )

        criteria_ranking_list = []
        for cname, entries in criterion_rankings.items():
            entries.sort(key=lambda x: x[1], reverse=True)
            best_team = entries[0][0] if entries else ""
            weakest_team = entries[-1][0] if entries else ""
            criteria_ranking_list.append({
                "criterion": cname,
                "rankings": [
                    {"team": t, "avg_score": s, "max_score": m}
                    for t, s, m in entries
                ],
                "best_team": best_team,
                "weakest_team": weakest_team,
            })

        criteria_ranking_list.sort(key=lambda x: x["criterion"])

        return {
            "teams": team_results,
            "criteria_rankings": criteria_ranking_list,
        }

    def get_team_analytics(self, team_id: str) -> dict:
        team = self.repo.get_team_by_id_or_code(team_id)
        if not team:
            return None

        tid = str(team.id)

        scores = self.repo.get_scores_for_team(tid)
        total_preds = len(scores)
        correct = sum(1 for s in scores if (s.winner_points or 0) > 0)
        avg_score = (
            round(sum(s.base_score or 0 for s in scores) / total_preds, 2)
            if total_preds
            else None
        )
        winner_acc = round((correct / total_preds) * 100, 1) if total_preds else None

        lb = self.repo.get_leaderboard_entry_for_team(tid)

        fallback_criteria = self._load_criteria_config()
        evals = self.repo.get_presentation_evaluations_for_team(tid)
        
        criteria_agg = {}
        for ev in evals:
            criteria_config = ev.presentation_criteria_config or fallback_criteria
            max_by_name = {c["name"]: c["max_score"] for c in criteria_config}

            judge_scores = ev.judge_scores or []
            for j_score in judge_scores:
                if isinstance(j_score, dict) and "scores" in j_score:
                    s_dict = j_score["scores"]
                elif isinstance(j_score, dict):
                    s_dict = j_score
                else:
                    continue

                for cname, cval in s_dict.items():
                    try:
                        val = float(cval)
                    except (ValueError, TypeError):
                        continue
                    if cname not in criteria_agg:
                        criteria_agg[cname] = {"sum": 0.0, "count": 0, "max_score": 0}
                    criteria_agg[cname]["sum"] += val
                    criteria_agg[cname]["count"] += 1
                    criteria_agg[cname]["max_score"] = max(
                        criteria_agg[cname]["max_score"], max_by_name.get(cname, 0)
                    )

        strengths = []
        weaknesses = []
        if criteria_agg:
            items = []
            for cname, data in criteria_agg.items():
                if not data["count"]:
                    continue
                avg = round(data["sum"] / data["count"], 2)
                mx = data["max_score"]
                pct = round((avg / mx) * 100, 1) if mx else 0.0
                items.append({"criterion": cname, "score": avg, "max_score": mx, "pct": pct})

            if items:
                best = max(items, key=lambda x: x["pct"])
                worst = min(items, key=lambda x: x["pct"])
                strengths = [best]
                weaknesses = [worst]

        return {
            "team_name": team.name,
            "scores_breakdown": {
                "total_predictions": total_preds,
                "correct_predictions": correct,
                "average_score": avg_score,
                "winner_accuracy_pct": winner_acc,
            },
            "leaderboard": {
                "rank": lb.rank,
                "phase1_score": lb.phase1_score,
                "technical_score": lb.technical_score,
                "presentation_score": lb.presentation_score,
                "final_score": lb.final_score,
            }
            if lb
            else None,
            "strengths": strengths,
            "weaknesses": weaknesses,
        }

    def get_judge_analytics(self) -> dict:
        evals = self.repo.get_all_presentation_evaluations()
        judges = self.repo.get_all_judges()
        judge_map = {str(j.id): j.name for j in judges}
        
        fallback_criteria = self._load_criteria_config()
        default_max_scores = {c["name"]: c["max_score"] for c in fallback_criteria}
        
        judge_scores = defaultdict(list)
        judge_criteria_scores = defaultdict(lambda: defaultdict(list))
        
        for ev in evals:
            criteria_config = ev.presentation_criteria_config or fallback_criteria
            max_by_name = {c["name"]: c["max_score"] for c in criteria_config}
            
            j_scores = ev.judge_scores or []
            for j_score in j_scores:
                judge_id = j_score.get("judge_id")
                if not judge_id:
                    continue
                
                # Fetch judge name from the database map
                judge_name = judge_map.get(str(judge_id), j_score.get("judge_name", f"Judge {judge_id}"))
                
                s_dict = j_score.get("scores", {})
                if not s_dict and "Problem Understanding" in j_score:
                    s_dict = {k: v for k, v in j_score.items() if k not in ["judge_id", "judge_name", "weighted_score", "multiplier", "grade", "raw_score"]}
                    
                total_given = 0.0
                has_scores = False
                for cname, cval in s_dict.items():
                    try:
                        val = float(cval)
                        total_given += val
                        has_scores = True
                        
                        max_score = max_by_name.get(cname, default_max_scores.get(cname, 0))
                        if max_score > 0:
                            pct = (val / max_score) * 100
                            judge_criteria_scores[judge_id][cname].append(pct)
                    except (ValueError, TypeError):
                        continue
                
                if has_scores:
                    judge_scores[judge_id].append({
                        "name": judge_name,
                        "total": total_given,
                        "team_id": ev.team_id
                    })
                    
        if not judge_scores:
            return {"summaries": [], "criteria_patterns": []}
            
        summaries = []
        criteria_patterns = []
        
        all_averages = []
        
        for judge_id, scores_list in judge_scores.items():
            judge_name = scores_list[0]["name"]
            totals = [s["total"] for s in scores_list]
            avg_score = round(sum(totals) / len(totals), 2)
            high_score = round(max(totals), 2)
            low_score = round(min(totals), 2)
            
            mean = sum(totals) / len(totals)
            variance = sum((x - mean) ** 2 for x in totals) / len(totals)
            
            all_averages.append((judge_id, avg_score))
            
            summaries.append({
                "judge_id": str(judge_id),
                "judge_name": judge_name,
                "average_score_given": avg_score,
                "highest_score_given": high_score,
                "lowest_score_given": low_score,
                "scoring_range": f"{low_score} - {high_score}",
                "variance": round(variance, 2),
                "evaluations_count": len(totals)
            })
            
            crit_averages = []
            for cname, cscores in judge_criteria_scores[judge_id].items():
                c_avg = round(sum(cscores) / len(cscores), 2)
                crit_averages.append({"criterion": cname, "average_score": c_avg})
            
            if crit_averages:
                crit_averages.sort(key=lambda x: x["average_score"])
                lowest_cat = crit_averages[0]["criterion"]
                strongest_cat = crit_averages[-1]["criterion"]
            else:
                lowest_cat = None
                strongest_cat = None
                
            criteria_patterns.append({
                "judge_id": str(judge_id),
                "judge_name": judge_name,
                "strongest_scoring_category": strongest_cat,
                "lowest_scoring_category": lowest_cat,
                "criteria_averages": crit_averages
            })
            
        if len(all_averages) > 0:
            avg_scores = [x[1] for x in all_averages]
            max_avg = max(avg_scores)
            min_avg = min(avg_scores)
            
            for s in summaries:
                if max_avg == min_avg:
                    s["strictness_level"] = "Balanced evaluator"
                elif s["average_score_given"] >= max_avg - (max_avg - min_avg) * 0.33:
                    s["strictness_level"] = "Generous evaluator"
                elif s["average_score_given"] <= min_avg + (max_avg - min_avg) * 0.33:
                    s["strictness_level"] = "Strict evaluator"
                else:
                    s["strictness_level"] = "Balanced evaluator"
                    
        return {
            "summaries": sorted(summaries, key=lambda x: x["average_score_given"], reverse=True),
            "criteria_patterns": criteria_patterns
        }
