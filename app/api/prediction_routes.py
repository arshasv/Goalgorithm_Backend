import uuid as uuid_lib
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.match import MatchModel
from app.models.prediction import PredictionModel
from app.models.team import TeamModel
from app.models.user import UserModel
from app.schemas import PredictionSubmission
from app.services.prediction_service import PredictionService

router = APIRouter(tags=["predictions"])


def _normalize_goal_scorers(payload: dict) -> dict:
    """Normalize dict-type entries in goal_scorers to plain name strings.
    Handles both the new format (objects with 'name', 'player_name' keys)
    and legacy format (strings)."""
    mp = payload.get("match_prediction")
    if mp is None:
        return payload

    gs = mp.get("goal_scorers")
    if not isinstance(gs, dict):
        return payload

    for side in ("home", "away"):
        raw_list = gs.get(side, [])
        if not isinstance(raw_list, list):
            continue
        normalized = []
        for entry in raw_list:
            if isinstance(entry, str):
                normalized.append(entry)
            elif isinstance(entry, dict):
                name = entry.get("name") or entry.get("player_name") or ""
                if name:
                    normalized.append(name)
            else:
                normalized.append(str(entry))
        gs[side] = normalized

    return payload


def _normalize_ai_output(raw: dict) -> dict:
    """
    Detect whether the payload is the new AI model output format
    (containing an "output" wrapper or top-level score_prediction / goal_insights keys)
    and normalize it into the legacy PredictionSubmission structure.

    New AI model output format (top-level or wrapped in "output"):
      match_prediction.win_probabilities.home_team.probability
      score_prediction.predicted_scoreline.home_goals / away_goals
      goal_insights.first_team_to_score / both_teams_to_score
      player_prediction.home_team.goal[] / player_prediction.away_team.goal[]
      player_prediction.home_team.clean_sheet_prediction
      player_prediction.away_team.clean_sheet_prediction

    Returns the normalized dict ready for PredictionSubmission Pydantic parsing.
    Preserves non-prediction envelope fields (team_id, match_id, submission_id, etc.).
    """
    # Preserve envelope fields
    team_id = raw.get("team_id", "")
    match_id = raw.get("match_id", "")
    submission_id = raw.get("submission_id", f"sub-json-{uuid_lib.uuid4()}")
    idempotency_key = raw.get("idempotency_key")

    # Check for new AI model output format:
    # Either wrapped under "output" key, or directly has score_prediction/goal_insights
    inner = raw.get("output", raw)

    has_score_prediction = "score_prediction" in inner
    has_goal_insights = "goal_insights" in inner
    has_player_prediction = "player_prediction" in inner
    has_win_probabilities = (
        "match_prediction" in inner
        and "win_probabilities" in inner.get("match_prediction", {})
    )

    # Detect new format: must have at least one of these new-format keys
    is_new_format = has_score_prediction or has_goal_insights or has_player_prediction or has_win_probabilities

    if not is_new_format:
        # Not the full AI format, but may still have dict-type goal_scorers.
        # Normalize any dict entries in goal_scorers to plain name strings.
        return _normalize_goal_scorers(raw)

    # ---- New AI model output format: normalize to legacy schema ----
    mp_raw = inner.get("match_prediction", {})
    score_pred = inner.get("score_prediction", {})
    goal_insights = inner.get("goal_insights", {})
    player_pred_raw = inner.get("player_prediction", {})

    # 1. Win probabilities → legacy probabilities
    win_probs = mp_raw.get("win_probabilities", {})
    home_prob = win_probs.get("home_team", {}).get("probability", 0)
    draw_prob = win_probs.get("draw", {}).get("probability", 0)
    away_prob = win_probs.get("away_team", {}).get("probability", 0)

    # Determine predicted_winner
    probs_map = {"home": home_prob, "draw": draw_prob, "away": away_prob}
    predicted_winner = max(probs_map, key=probs_map.get)

    # 2. Score prediction → predicted_scoreline
    scoreline_raw = score_pred.get("predicted_scoreline", {})
    home_goals = int(scoreline_raw.get("home_goals", 0))
    away_goals = int(scoreline_raw.get("away_goals", 0))
    home_team_name = scoreline_raw.get("home_team")
    away_team_name = scoreline_raw.get("away_team")
    total_goals = score_pred.get("total_goals", home_goals + away_goals)

    # 3. Goal insights
    fts_raw = goal_insights.get("first_team_to_score", {})
    first_team_obj = {}
    if fts_raw:
        team_val = fts_raw.get("team", "")
        # Normalize team name → "home"/"away" if possible
        if team_val == home_team_name:
            normalized_team = "home"
        elif team_val == away_team_name:
            normalized_team = "away"
        else:
            normalized_team = team_val.lower() if team_val else "home"
        first_team_obj = {
            "team": normalized_team,
            "probability": fts_raw.get("probability", 0),
        }

    btts_raw = goal_insights.get("both_teams_to_score", {})
    btts_obj = btts_raw if btts_raw else {}

    # 4. Player predictions + clean sheet
    player_predictions = []
    clean_sheet_predictions = []
    goal_scorers = {"home": [], "away": []}

    for side_key, side_label in [("home_team", "home"), ("away_team", "away")]:
        side_data = player_pred_raw.get(side_key, {})

        # Goal scorers
        goal_list = side_data.get("goal", [])
        for p in goal_list:
            name = p.get("name")
            preds = p.get("predictions", [])
            if not name or not preds:
                continue
            best = max(preds, key=lambda x: x.get("probability", 0))
            predicted_goals = best.get("goal_count", 0)
            goal_prob = best.get("probability", 0)
            player_predictions.append({
                "player_name": name,
                "team": side_label,
                "predicted_goals": predicted_goals,
                "goal_probability": goal_prob,
                "probability": goal_prob,
            })
            goal_scorers[side_label].append(name)

        # Clean sheet
        cs = side_data.get("clean_sheet_prediction", {})
        if cs and (cs.get("goalkeeper") or cs.get("prediction") is not None):
            clean_sheet_predictions.append(cs)

    normalized = {
        "team_id": team_id,
        "match_id": match_id,
        "submission_id": submission_id,
        "idempotency_key": idempotency_key,
        "match_prediction": {
            "predicted_winner": predicted_winner,
            "predicted_scoreline": {
                "home_team_goals": home_goals,
                "away_team_goals": away_goals,
            },
            "probabilities": {
                "home_win_probability": home_prob,
                "draw_probability": draw_prob,
                "away_win_probability": away_prob,
            },
            "total_goals_prediction": total_goals,
            "first_team_to_score": first_team_obj or None,
            "both_teams_to_score": btts_obj or None,
            "clean_sheet_predictions": clean_sheet_predictions,
            "goal_scorers": goal_scorers,
        },
        "player_predictions": player_predictions,
    }

    return normalized


@router.get("/predictions")
def list_predictions(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    teams = db.query(TeamModel).all()
    team_by_uuid = {str(t.id): t for t in teams}
    team_by_letter = {t.team_id: t for t in teams}

    # Build match lookup: match_id (string like "M32") → readable label
    matches = db.query(MatchModel).all()
    match_by_id = {str(m.id): m for m in matches}
    # Also index by match_number string for legacy IDs
    match_by_num = {f"M{m.match_number}": m for m in matches if m.match_number}

    if str(current_user.role).upper() == UserRole.ORGANIZER.value:
        predictions = db.query(PredictionModel).all()
    else:
        team = db.query(TeamModel).filter(TeamModel.user_id == current_user.id).first()
        if team:
            predictions = (
                db.query(PredictionModel)
                .filter(PredictionModel.team_id == team.id)
                .all()
            )
        else:
            predictions = []

    from app.models.score import ScoreModel
    scores = db.query(ScoreModel.team_id, ScoreModel.match_id).all()
    scored_set = {(str(s.team_id), str(s.match_id)) for s in scores}

    result = []
    for p in predictions:
        tm = team_by_uuid.get(str(p.team_id)) or team_by_letter.get(str(p.team_id))
        # Resolve match to human-readable name
        match_obj = match_by_id.get(str(p.match_id)) or match_by_num.get(str(p.match_id))
        if match_obj:
            match_label = f"M{match_obj.match_number}: {match_obj.home_team_name} vs {match_obj.away_team_name}"
        else:
            match_label = str(p.match_id)

        # Check actual scoring status
        if (str(p.team_id), str(p.match_id)) in scored_set:
            display_status = "SCORED"
        else:
            display_status = p.status.value if p.status else None

        result.append({
            "id": str(p.id),
            "team_id": str(p.team_id),
            "team_code": tm.team_id if tm else '',
            "team_name": tm.name if tm else '',
            "team_leader_name": tm.team_leader_name if tm else '',
            "match_id": p.match_id,
            "match_label": match_label,
            "submission_id": p.submission_id,
            "idempotency_key": p.idempotency_key,
            "status": display_status,
            "match_prediction": {
                "predicted_winner": p.predicted_winner.value if p.predicted_winner else None,
                "predicted_scoreline": {
                    "home_team_goals": p.predicted_home_goals,
                    "away_team_goals": p.predicted_away_goals,
                },
                "probabilities": {
                    "home_win_probability": p.home_win_probability,
                    "draw_probability": p.draw_probability,
                    "away_win_probability": p.away_win_probability,
                },
                "total_goals_prediction": p.total_goals_prediction,
                # Goal insights
                "both_teams_to_score": {
                    "prediction": p.both_teams_to_score_prediction,
                    "probability": p.both_teams_to_score_probability,
                },
                "first_team_to_score": {
                    "team": p.first_goal_team.value if p.first_goal_team else None,
                    "probability": p.first_goal_team_probability,
                },
                # Legacy flat fields (kept for backward compat)
                "first_goal_team": p.first_goal_team.value if p.first_goal_team else None,
                "both_teams_to_score_probability": p.both_teams_to_score_probability,
                # Clean sheet predictions
                "clean_sheet_predictions": p.clean_sheet_predictions or [],
                # Legacy flat clean sheet (for backward compat)
                "clean_sheet_probability": {
                    "home_team": p.home_clean_sheet_probability,
                    "away_team": p.away_clean_sheet_probability,
                },
                "goal_scorers": p.goal_scorers or {},
            },
            "player_predictions": [
                {
                    "player_name": pp.player_name,
                    "team": pp.team,
                    "predicted_goals": pp.predicted_goals,
                    "probability": pp.goal_probability,
                    # Legacy fields
                    "player_id": pp.player_id,
                    "goal_probability": pp.goal_probability,
                    "assist_probability": pp.assist_probability,
                }
                for pp in p.player_predictions
            ] if p.player_predictions else [],
            "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
        })
    return result



@router.post("/predictions")
async def submit_prediction(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Submit a match prediction. Accepts two formats automatically:
    
    1. **Legacy / Manual format**: Standard PredictionSubmission with match_prediction.predicted_scoreline,
       match_prediction.probabilities, and player_predictions[].player_name.
    
    2. **New AI model output format**: JSON with an "output" wrapper (or top-level) containing
       score_prediction, goal_insights, player_prediction, and match_prediction.win_probabilities.
       The system automatically detects and normalizes the new format.
    
    No manual conversion required.
    """
    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid JSON body.")

    # Detect and normalize AI model output format → legacy schema
    try:
        normalized = _normalize_ai_output(raw_body)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported JSON structure. Expected either the legacy prediction schema or the official AI model output schema. Details: {str(e)}"
        )

    # Parse with Pydantic
    try:
        payload = PredictionSubmission(**normalized)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Resolve team from authenticated user or organizer override
    if str(current_user.role).upper() == UserRole.ORGANIZER.value:
        try:
            team_uuid = uuid_lib.UUID(payload.team_id)
            team = db.query(TeamModel).filter(TeamModel.id == team_uuid).first()
        except ValueError:
            team = db.query(TeamModel).filter(TeamModel.team_id == payload.team_id).first()
        if not team:
            raise HTTPException(status_code=400, detail=f"Team not found for given team_id: {payload.team_id}")
    else:
        team = db.query(TeamModel).filter(TeamModel.user_id == current_user.id).first()
        if not team:
            raise HTTPException(status_code=400, detail="Team not found for current user")

    payload.team_id = str(team.id)
    service = PredictionService(db)
    return service.save_prediction(payload.model_dump())
