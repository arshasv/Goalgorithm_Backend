MAX_PROBABILITY_SCORE = 5.0


def _tiered_score(accuracy: float, high: float, medium: float, low: float) -> float:
    if accuracy >= 70:
        return high
    elif accuracy >= 50:
        return medium
    elif accuracy >= 30:
        return low
    return 0.0


def calculate_probability_score(
    prediction: dict,
    actual_result: dict,
    config: dict | None = None,
) -> float:
    mp = prediction["match_prediction"]
    actual_scoreline = actual_result.get("final_score", {})
    actual_home = actual_scoreline.get("home_team_goals", 0)
    actual_away = actual_scoreline.get("away_team_goals", 0)
    actual_winner = actual_result.get("actual_winner", "draw")
    probs = mp.get("probabilities", {})

    # Winner Confidence (max 2)
    if actual_winner == "home":
        winner_accuracy = probs.get("home_win_probability", 0)
    elif actual_winner == "away":
        winner_accuracy = probs.get("away_win_probability", 0)
    else:
        winner_accuracy = probs.get("draw_probability", 0)

    winner_confidence = _tiered_score(winner_accuracy, 2.0, 1.5, 1.0)

    # BTTS Probability (max 1)
    actual_btts = actual_home > 0 and actual_away > 0
    pred_btts = None
    btts_prob = 0
    btts = mp.get("both_teams_to_score")
    if btts and isinstance(btts, dict) and "prediction" in btts:
        pred_btts = btts["prediction"]
        btts_prob = btts.get("probability", 0)
    elif mp.get("both_teams_to_score_probability") is not None:
        btts_prob = mp["both_teams_to_score_probability"]
        pred_btts = btts_prob > 50.0

    if pred_btts is not None:
        p_btts = btts_prob if pred_btts else 100.0 - btts_prob
        btts_accuracy = p_btts if actual_btts else 100.0 - p_btts
    else:
        btts_accuracy = 0

    btts_probability = _tiered_score(btts_accuracy, 1.0, 0.75, 0.5)

    # First Team To Score Probability (max 2)
    actual_first_team = actual_result.get("first_team_to_score", "none").lower()
    pred_first_team = None
    first_team_prob = 0

    if mp.get("first_team_to_score") is not None:
        pred_first_team = mp["first_team_to_score"]["team"].lower()
        first_team_prob = mp["first_team_to_score"].get("probability", 0)
    elif mp.get("first_goal_team") is not None:
        pred_first_team = mp["first_goal_team"].lower()
        first_team_prob = mp.get("first_goal_team_probability", 0)

    if pred_first_team is not None and pred_first_team == actual_first_team:
        first_team_accuracy = first_team_prob
    else:
        first_team_accuracy = 0

    first_team_probability = _tiered_score(first_team_accuracy, 2.0, 1.5, 1.0)

    total = winner_confidence + btts_probability + first_team_probability
    return min(total, MAX_PROBABILITY_SCORE)
