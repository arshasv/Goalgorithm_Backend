ALL_SCORERS_CORRECT = 2.5
HALF_SCORERS_CORRECT = 1.5
AT_LEAST_ONE_CORRECT = 1.0
NO_SCORER_CORRECT = 0.0
CLEAN_SHEET_BOTH = 2.5
CLEAN_SHEET_ONE = 1.0
CLEAN_SHEET_NONE = 0.0
MAX_PLAYER_SCORE = 5.0


def _normalize_scorer(entry):
    if isinstance(entry, str):
        return entry.lower().strip()
    if isinstance(entry, dict):
        name = entry.get("name") or entry.get("player_name") or ""
        return name.lower().strip()
    return str(entry).lower().strip()


def calculate_player_score(
    prediction: dict,
    actual_result: dict,
    config: dict | None = None,
) -> float:
    mp = prediction["match_prediction"]

    # Goal Scorer Prediction (max 2.5)
    pred_scorers = mp.get("goal_scorers", {})
    predicted_home_scorers = [_normalize_scorer(s) for s in pred_scorers.get("home", [])]
    predicted_away_scorers = [_normalize_scorer(s) for s in pred_scorers.get("away", [])]

    actual_scorers = actual_result.get("goal_scorers", {})
    actual_home_scorers = [_normalize_scorer(s) for s in actual_scorers.get("home", [])]
    actual_away_scorers = [_normalize_scorer(s) for s in actual_scorers.get("away", [])]

    all_actual_scorers = set(actual_home_scorers + actual_away_scorers)
    all_predicted_scorers = set(predicted_home_scorers + predicted_away_scorers)

    if not all_actual_scorers and not all_predicted_scorers:
        goal_scorer_points = ALL_SCORERS_CORRECT
    elif not all_predicted_scorers:
        goal_scorer_points = NO_SCORER_CORRECT
    else:
        correct_scorers = all_predicted_scorers & all_actual_scorers
        if correct_scorers == all_actual_scorers and correct_scorers == all_predicted_scorers:
            goal_scorer_points = ALL_SCORERS_CORRECT
        elif len(correct_scorers) >= max(len(all_actual_scorers), 1) / 2:
            goal_scorer_points = HALF_SCORERS_CORRECT
        elif len(correct_scorers) >= 1:
            goal_scorer_points = AT_LEAST_ONE_CORRECT
        else:
            goal_scorer_points = NO_SCORER_CORRECT

    # Clean Sheet Prediction (max 2.5)
    actual_scoreline = actual_result.get("final_score", {})
    actual_home_conceded = actual_scoreline.get("away_team_goals", 0)
    actual_away_conceded = actual_scoreline.get("home_team_goals", 0)

    actual_home_cs = actual_away_conceded == 0
    actual_away_cs = actual_home_conceded == 0

    pred_home_cs = None
    pred_away_cs = None

    cs_preds = mp.get("clean_sheet_predictions")
    if cs_preds and isinstance(cs_preds, list) and len(cs_preds) >= 2:
        pred_home_cs = cs_preds[0].get("prediction", False)
        pred_away_cs = cs_preds[1].get("prediction", False)
    else:
        legacy_cs = mp.get("clean_sheet_probability", {})
        if isinstance(legacy_cs, dict):
            pred_home_cs = legacy_cs.get("home_team", 0) >= 50.0
            pred_away_cs = legacy_cs.get("away_team", 0) >= 50.0

    if pred_home_cs is not None and pred_away_cs is not None:
        home_correct = pred_home_cs == actual_home_cs
        away_correct = pred_away_cs == actual_away_cs
        if home_correct and away_correct:
            clean_sheet_points = CLEAN_SHEET_BOTH
        elif home_correct or away_correct:
            clean_sheet_points = CLEAN_SHEET_ONE
        else:
            clean_sheet_points = CLEAN_SHEET_NONE
    else:
        clean_sheet_points = CLEAN_SHEET_NONE

    total = goal_scorer_points + clean_sheet_points
    return min(total, MAX_PLAYER_SCORE)
