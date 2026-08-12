def calculate_total_goals_score(prediction: dict, actual_result: dict, config: dict | None = None) -> float:
    points_exact = config.get("total_goals_points_exact", 5.0) if config else 5.0
    points_wrong = config.get("total_goals_points_wrong", 0.0) if config else 0.0
    
    pred_total = prediction["match_prediction"].get("total_goals_prediction")
    if pred_total is None:
        return float(points_wrong)
        
    actual_scoreline = actual_result["final_score"]
    actual_total = actual_scoreline["home_team_goals"] + actual_scoreline["away_team_goals"]
    
    if pred_total == actual_total:
        return float(points_exact)
    return float(points_wrong)
