from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
import csv
import io

from app.api.deps import get_current_organizer
from app.database.session import get_db
from app.schemas import (
    ActualResultSubmission,
    PredictionSubmission,
    PresentationEvaluation,
    TechnicalEvaluation,
)
from app.services.scoring_service import ScoringService

router = APIRouter(tags=["scoring"])


class MatchScoreRequest(BaseModel):
    prediction: PredictionSubmission
    actual_result: ActualResultSubmission


@router.post("/calculate-match-score")
def calculate_match_score(
    payload: MatchScoreRequest,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    service = ScoringService(db)
    return service.calculate_and_save_match_score(
        payload.prediction.model_dump(),
        payload.actual_result.model_dump(),
    )


@router.post("/technical-score")
def calculate_technical(
    evaluation: TechnicalEvaluation,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    service = ScoringService(db)
    res = service.calculate_and_save_technical_score(evaluation.model_dump())
    service.compute_and_save_leaderboard(None)
    return res


@router.post("/presentation-score")
def calculate_presentation(
    evaluations: list[PresentationEvaluation],
    round_id: str | None = None,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    service = ScoringService(db)
    res = service.calculate_and_save_presentation_scores(
        [ev.model_dump() for ev in evaluations], round_id
    )
    service.compute_and_save_leaderboard(None)
    return res

@router.post("/presentation-score/upload-csv")
def upload_presentation_csv(
    file: UploadFile = File(...),
    round_id: str | None = Form(None),
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    content = file.file.read()
    buffer = io.StringIO(content.decode('utf-8'))
    reader = csv.DictReader(buffer)
    
    from app.models.team import TeamModel
    from app.models.judge import JudgeModel
    
    import re
    def normalize_team_name(name: str) -> str:
        n = str(name).lower().strip()
        n = re.sub(r'^team\s+', '', n)
        n = re.sub(r'[-\u2013\u2014]', '-', n)
        n = re.sub(r'\s*-\s*', '-', n)
        return n
        
    def normalize_judge_name(name: str) -> str:
        n = str(name).lower().strip()
        # Remove anything in parentheses
        n = re.sub(r'\(.*?\)', '', n).strip()
        return n
        
    db_teams = db.query(TeamModel).all()
    db_judges = db.query(JudgeModel).all()
    
    from app.services.scoring_service import ScoringService, _load_active_config
    
    service = ScoringService(db)
    config, _ = _load_active_config(db)
    criteria = config.get("presentation_criteria", []) if config else []
    if not criteria:
        criteria = [
            {"name": "Problem Understanding", "max_score": 10},
            {"name": "Feature Engineering", "max_score": 15},
            {"name": "Team Work", "max_score": 10},
            {"name": "Presentation Quality", "max_score": 10},
            {"name": "Q&A", "max_score": 5}
        ]
    
    eval_map = {}
    processed = 0
    failed = 0
    errors = []
    
    try:
        for row_idx, row in enumerate(reader):
            team_name = str(row.get("Team Name", "")).strip()
            judge_name = str(row.get("Judge Name", "")).strip()
            
            team_id = None
            norm_csv_team = normalize_team_name(team_name)
            
            for t in db_teams:
                norm_db = normalize_team_name(t.name)
                if norm_csv_team and (norm_csv_team == norm_db or norm_csv_team in norm_db or norm_db in norm_csv_team):
                    team_id = str(t.id)
                    break
                    
            judge_id = None
            norm_csv_judge = normalize_judge_name(judge_name)
            raw_csv_judge = str(judge_name).lower().strip()
            
            for j in db_judges:
                norm_db_judge = normalize_judge_name(j.name)
                # Check for "Sayooj V.V (Judge1)" vs "Judge1" vs "Sayooj V.V"
                if raw_csv_judge in j.name.lower() or j.name.lower() in raw_csv_judge or norm_csv_judge == norm_db_judge:
                    judge_id = str(j.id)
                    break
            
            if not team_id:
                errors.append(f"Row {row_idx + 2}: Unknown team '{team_name}'")
                failed += 1
                continue
            if not judge_id:
                errors.append(f"Row {row_idx + 2}: Unknown judge '{judge_name}'")
                failed += 1
                continue
            
            scores = {}
            row_valid = True
            for c in criteria:
                c_name = c["name"].strip()
                # Handle exact match or fuzzy match (e.g., trailing spaces)
                val = None
                for key in row.keys():
                    if key and key.strip() == c_name:
                        val = row[key]
                        break
                        
                if val is not None and str(val).strip() != "":
                    try:
                        scores[c["name"]] = float(val)
                    except ValueError:
                        errors.append(f"Row {row_idx + 2}: Invalid score for {c_name}")
                        row_valid = False
                else:
                    scores[c["name"]] = 0.0
                    
            if row_valid:
                if team_id not in eval_map:
                    eval_map[team_id] = []
                eval_map[team_id].append({"judge_id": judge_id, "scores": scores})
                processed += 1
            else:
                failed += 1
                
        if eval_map:
            evals_list = []
            for tid, j_scores in eval_map.items():
                evals_list.append({
                    "team_id": tid,
                    "judge_scores": j_scores
                })
            service.calculate_and_save_presentation_scores(evals_list, round_id)
            service.compute_and_save_leaderboard(None)
            
    except Exception as e:
        errors.append(f"Server error during processing: {str(e)}")
        failed += 1
        
    return {"message": "CSV processed successfully", "processed": processed, "failed": failed, "errors": errors}

@router.post("/presentation-score/reset")
def reset_presentation_scores(
    round_id: str | None = None,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    from app.models.evaluation import PresentationEvaluationModel
    
    query = db.query(PresentationEvaluationModel)
    if round_id:
        query = query.filter(PresentationEvaluationModel.round_id == round_id)
        
    evals = query.all()
    count = len(evals)
    for ev in evals:
        ev.judge_scores = None
        ev.raw_total = None
        ev.presentation_score = None
        ev.rank = None
        ev.grade = None
        ev.multiplier = None
        ev.judge_count = None
        ev.max_marks = None
        ev.presentation_criteria_config = None
    db.commit()
    
    service = ScoringService(db)
    service.compute_and_save_leaderboard(None)
    
    return {"message": "Presentation scores reset successfully", "count": count}

@router.get("/presentation-score/template")
def download_presentation_template():
    content = "Team Name,Judge Name,Problem Understanding,Feature Engineering,Team Work,Presentation Quality,Q&A\n"
    return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=presentation_scores_template.csv"})

@router.post("/matches/{match_id}/calculate-scores")
def calculate_all_scores_for_match(
    match_id: str,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    from app.models.prediction import PredictionModel
    from app.models.actual_result import ActualResultModel
    from app.models.score import ScoreModel
    from app.models.enums import Grade
    from fastapi import HTTPException
    import traceback
    import logging
    import uuid

    logger = logging.getLogger(__name__)
    match_uuid = uuid.UUID(match_id)

    try:
        logger.info("=== DIAGNOSTICS: calculate_all_scores_for_match START ===")
        logger.info("Requested match_id: %s", match_id)
        
        from app.models.match import MatchModel
        match_exists = db.query(MatchModel).filter(MatchModel.id == match_uuid).first() is not None
        logger.info("Does match exist in matches table?: %s", "YES" if match_exists else "NO")

        existing_count = db.query(ScoreModel).filter(ScoreModel.match_id == match_uuid).count()
        logger.info("Number of existing score rows: %s", existing_count)

        actual = db.query(ActualResultModel).filter(ActualResultModel.match_id == match_uuid).first()
        logger.info("Number of actual results found: %s", 1 if actual else 0)
        
        if not actual:
            logger.info("=== DIAGNOSTICS END: Missing Actual Result ===")
            raise HTTPException(status_code=400, detail="Actual result not found for this match.")

        predictions = db.query(PredictionModel).filter(PredictionModel.match_id == match_uuid).all()
        logger.info("Number of predictions found: %s", len(predictions))
        
        if not predictions:
            logger.info("=== DIAGNOSTICS END: No Predictions ===")
            return {"status": "no_predictions", "calculated_count": 0}

        # Pre-build actual result payload to avoid session expiration issues later
        actual_payload = {
            "match_id": actual.match_id,
            "actual_winner": actual.actual_winner.value if actual.actual_winner else "draw",
            "final_score": {
                "home_team_goals": actual.actual_home_goals or 0,
                "away_team_goals": actual.actual_away_goals or 0
            },
            "goal_scorers": actual.goal_scorers or {"home": [], "away": []},
            "first_team_to_score": actual.first_team_to_score or "none",
            "player_results": [
                {
                    "player_id": pa.player_id,
                    "player_name": pa.player_name,
                    "actual_goals": pa.actual_goals or 0
                } for pa in actual.player_actuals
            ]
        }
        if not actual_payload["player_results"]:
            actual_payload["player_results"] = [{"player_id": "NONE", "player_name": "No Scorers", "actual_goals": 0}]

        # Pre-build prediction payloads
        pred_payloads = []
        for p in predictions:
            pred_payloads.append({
                "team_id": p.team_id,
                "match_id": p.match_id,
                "submission_id": p.id,
                "idempotency_key": p.id,
                "match_prediction": {
                    "predicted_winner": p.predicted_winner.value if p.predicted_winner else "draw",
                    "predicted_scoreline": {
                        "home_team_goals": p.predicted_home_goals or 0,
                        "away_team_goals": p.predicted_away_goals or 0
                    },
                    "probabilities": {
                        "home_win_probability": p.home_win_probability or 0.0,
                        "draw_probability": p.draw_probability or 0.0,
                        "away_win_probability": p.away_win_probability or 0.0
                    },
                    "clean_sheet_probability": {
                        "home_team": p.home_clean_sheet_probability or 0.0,
                        "away_team": p.away_clean_sheet_probability or 0.0
                    },
                    "first_goal_team": p.first_goal_team.value if p.first_goal_team else "none",
                    "first_goal_team_probability": p.first_goal_team_probability or 0.0,
                    "both_teams_to_score": {
                        "prediction": p.both_teams_to_score_prediction if p.both_teams_to_score_prediction is not None else False,
                        "probability": p.both_teams_to_score_probability or 0.0
                    },
                    "total_goals_prediction": p.total_goals_prediction or 0,
                    "goal_scorers": p.goal_scorers or {"home": [], "away": []}
                },
                "player_predictions": [
                    {
                        "player_id": pp.player_id or f"pp-{pp.player_name}",
                        "player_name": pp.player_name,
                        "goal_probability": pp.goal_probability or 0.0,
                        "predicted_goals": pp.predicted_goals or 0,
                        "assist_probability": pp.assist_probability or 0.0
                    } for pp in p.player_predictions
                ]
            })

        # Purge ALL existing scores for this match completely before recalculating
        # Use synchronize_session='fetch' to properly sync the session identity map
        delete_count = db.query(ScoreModel).filter(
            ScoreModel.match_id == match_uuid
        ).delete(synchronize_session='fetch')
        logger.info("Number deleted: %s", delete_count)
        db.commit()
        # Expire all session objects so no stale references remain
        db.expire_all()

        service = ScoringService(db)
        count = 0
        for pred_payload in pred_payloads:
            try:
                service.calculate_and_save_match_score(pred_payload, actual_payload)
                count += 1
            except Exception as e:
                logger.error(
                    "Unexpected error calculating score for match_id=%s, "
                    "team_id=%s, prediction_id=%s. "
                    "Exception: %s - %s\n%s",
                    match_id, pred_payload['team_id'], pred_payload['submission_id'],
                    type(e).__name__, str(e), traceback.format_exc()
                )
                raise HTTPException(status_code=500, detail="An internal server error occurred while calculating the score for a prediction.")

        # --- RELATIVE RANK MULTIPLIER ---
        scores = db.query(ScoreModel).filter(
            ScoreModel.match_id == match_uuid
        ).order_by(ScoreModel.base_score.desc()).all()

        logger.info(
            "match_id=%s | scores after recalculation=%s", match_id, len(scores)
        )

        current_rank = 1
        for i, s in enumerate(scores):
            if i > 0 and s.base_score == scores[i-1].base_score:
                pass
            else:
                current_rank = i + 1

            s.match_rank = current_rank

            if current_rank == 1:
                s.grade = Grade.A
                s.multiplier = 3
            elif current_rank in [2, 3, 4]:
                s.grade = Grade.B
                s.multiplier = 2
            else:
                s.grade = Grade.C
                s.multiplier = 1

            s.earned_points = s.base_score * s.multiplier

        db.commit()

        logger.info(
            "match_id=%s | before leaderboard recalculation", match_id
        )
        service.compute_and_save_leaderboard(None)
        logger.info("Number inserted: %s", count)
        logger.info("=== DIAGNOSTICS END: SUCCESS ===")
        return {"status": "success", "calculated_count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "=== DIAGNOSTICS: CRASH DETECTED ===\n"
            "filename: %s\n"
            "function: calculate_all_scores_for_match\n"
            "line number: %s\n"
            "exception type: %s\n"
            "exception message: %s\n"
            "complete traceback:\n%s",
            __file__, e.__traceback__.tb_lineno if e.__traceback__ else "unknown",
            type(e).__name__, str(e), traceback.format_exc()
        )
        db.rollback()
        raise HTTPException(status_code=500, detail="An internal server error occurred while calculating scores.")

@router.post("/reset-predictions")
def reset_predictions(
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    from app.models.score import ScoreModel
    from app.services.scoring_service import ScoringService
    
    # Delete all phase 1 scores
    deleted_count = db.query(ScoreModel).delete()
    db.commit()
    
    # Recalculate leaderboard
    service = ScoringService(db)
    service.compute_and_save_leaderboard(None)
    
    return {"message": "Prediction scores reset successfully", "deleted": deleted_count}


@router.post("/reset-all")
def reset_all_scores(
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    from app.models.score import ScoreModel
    from app.models.evaluation import TechnicalEvaluationModel, PresentationEvaluationModel
    from app.models.leaderboard import LeaderboardModel
    from app.services.scoring_service import ScoringService
    
    # Delete all score records
    db.query(ScoreModel).delete()
    db.query(TechnicalEvaluationModel).delete()
    db.query(PresentationEvaluationModel).delete()
    db.query(LeaderboardModel).delete()
    db.commit()
    
    # Recalculate leaderboard to re-initialize 0 values for all active teams
    service = ScoringService(db)
    service.compute_and_save_leaderboard(None)
    
    return {"message": "All scores and leaderboard reset successfully"}
