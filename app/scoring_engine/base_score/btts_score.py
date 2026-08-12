def calculate_btts_score(prediction: dict, actual_result: dict, config: dict | None = None) -> float:
    points_correct = config.get("btts_points_correct", 5.0) if config else 5.0
    points_incorrect = config.get("btts_points_incorrect", 0.0) if config else 0.0
    
    match_pred = prediction["match_prediction"]
    pred_btts = None
    
    if match_pred.get("both_teams_to_score") is not None:
        pred_btts = match_pred["both_teams_to_score"]["prediction"]
    elif match_pred.get("both_teams_to_score_probability") is not None:
        # Legacy fallback if they have a probability > 50% we assume true
        pred_btts = match_pred["both_teams_to_score_probability"] > 50.0
    
    if pred_btts is None:
        return float(points_incorrect)
        
    actual_scoreline = actual_result["final_score"]
    actual_btts = actual_scoreline["home_team_goals"] > 0 and actual_scoreline["away_team_goals"] > 0
    
    if pred_btts == actual_btts:
        return float(points_correct)
    return float(points_incorrect)
