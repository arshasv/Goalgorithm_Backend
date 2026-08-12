SCORELINE_EXACT = 7.5
SCORELINE_ONE_TEAM = 4.0
SCORELINE_GOAL_DIFF = 3.0
SCORELINE_INCORRECT = 0.0
BTTS_CORRECT = 2.5
BTTS_INCORRECT = 0.0
MAX_SCORELINE_SCORE = 10.0


def calculate_scoreline_score(
    prediction: dict,
    actual_result: dict,
    config: dict | None = None,
) -> float:
    mp = prediction["match_prediction"]
    pred_scoreline = mp.get("predicted_scoreline", {})
    actual_scoreline = actual_result.get("final_score", {})

    pred_home = pred_scoreline.get("home_team_goals", 0)
    pred_away = pred_scoreline.get("away_team_goals", 0)
    actual_home = actual_scoreline.get("home_team_goals", 0)
    actual_away = actual_scoreline.get("away_team_goals", 0)

    # Scoreline prediction (max 7.5)
    if (pred_home, pred_away) == (actual_home, actual_away):
        scoreline_points = SCORELINE_EXACT
    else:
        pred_margin = pred_home - pred_away
        actual_margin = actual_home - actual_away
        correct_home = pred_home == actual_home
        correct_away = pred_away == actual_away

        if correct_home or correct_away:
            scoreline_points = SCORELINE_ONE_TEAM
        elif pred_margin == actual_margin:
            scoreline_points = SCORELINE_GOAL_DIFF
        else:
            scoreline_points = SCORELINE_INCORRECT

    # BTTS (max 2.5)
    actual_btts = actual_home > 0 and actual_away > 0
    pred_btts = None
    btts = mp.get("both_teams_to_score")
    if btts and isinstance(btts, dict) and "prediction" in btts:
        pred_btts = btts["prediction"]
    elif mp.get("both_teams_to_score_probability") is not None:
        pred_btts = mp["both_teams_to_score_probability"] > 50.0

    if pred_btts == actual_btts:
        btts_points = BTTS_CORRECT
    else:
        btts_points = BTTS_INCORRECT

    total = scoreline_points + btts_points
    return min(total, MAX_SCORELINE_SCORE)
