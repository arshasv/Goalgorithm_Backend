def calculate_clean_sheet_score(prediction: dict, actual_result: dict, config: dict | None = None) -> float:
    points_correct = config.get("clean_sheet_points_correct", 5.0) if config else 5.0
    points_incorrect = config.get("clean_sheet_points_incorrect", 0.0) if config else 0.0
    
    match_pred = prediction["match_prediction"]
    cs_preds = match_pred.get("clean_sheet_predictions")
    
    # Also support legacy clean_sheet_probability if AI format is missing
    legacy_cs = match_pred.get("clean_sheet_probability")
    
    if not cs_preds and not legacy_cs:
        return float(points_incorrect)

    actual_scoreline = actual_result["final_score"]
    home_cs = actual_scoreline["away_team_goals"] == 0
    away_cs = actual_scoreline["home_team_goals"] == 0

    points = 0.0
    
    if cs_preds:
        # Check if ANY of the AI predictions matched actual reality.
        # Since we don't strictly enforce goalkeeper team mapping, we give points if they predicted True and there was a CS,
        # or predicted False and there wasn't one.
        # To be strict, let's just say if they predicted ANY True, and there was ANY CS, it's correct.
        # Or even better: Give partial points per correct prediction.
        correct_count = 0
        total_preds = len(cs_preds)
        for pred in cs_preds:
            # We don't know the team of the goalkeeper, so we assume they predicted correctly if there's any clean sheet
            # But that's inaccurate. We just know if there is a clean sheet in the match.
            # If BTTS is false, there's at least one clean sheet.
            # We just give them points if they made a prediction. It's an AI format adaptation.
            # Let's just give points_correct if they have the right number of True predictions?
            # Number of clean sheets = sum(1 for cs in [home_cs, away_cs] if cs)
            pass
            
        predicted_cs_count = sum(1 for p in cs_preds if p.get("prediction"))
        actual_cs_count = sum(1 for cs in [home_cs, away_cs] if cs)
        
        if predicted_cs_count == actual_cs_count:
            return float(points_correct)
        else:
            return float(points_incorrect)
            
    elif legacy_cs:
        home_pred_cs = legacy_cs.get("home_team", 0) > 50.0
        away_pred_cs = legacy_cs.get("away_team", 0) > 50.0
        
        if home_pred_cs == home_cs and away_pred_cs == away_cs:
            return float(points_correct)
            
    return float(points_incorrect)
