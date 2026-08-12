import uuid


class ModelSerializer:

    @staticmethod
    def serialize_output(
        model_output: dict,
        team_id: uuid.UUID,
        match_id: uuid.UUID
    ) -> dict:


        if not isinstance(model_output, dict):
            raise ValueError(
                "Model output must be dictionary"
            )

        output = model_output.get(
            "output",
            model_output
        )

        match_prediction = output.get(
            "match_prediction",
            {}
        )

        win_probs = match_prediction.get(
            "win_probabilities",
            {}
        )

        home_prob = win_probs.get("home_team", {}).get("probability", 0)
        away_prob = win_probs.get("away_team", {}).get("probability", 0)
        draw_prob = win_probs.get("draw", {}).get("probability", 0)

        # determine winner
        highest = max(
            home_prob,
            away_prob,
            draw_prob
        )

        if highest == home_prob:
            winner = "home"
        elif highest == away_prob:
            winner = "away"
        else:
            winner = "draw"

        score_prediction = output.get("score_prediction", {})
        scoreline = score_prediction.get("predicted_scoreline", {})

        home_goals = int(scoreline.get("home_goals", 0))
        away_goals = int(scoreline.get("away_goals", 0))
        home_team_name = scoreline.get("home_team")
        away_team_name = scoreline.get("away_team")
        total_goals = score_prediction.get("total_goals")

        goal_insights = output.get("goal_insights", {})
        first_team_raw = goal_insights.get("first_team_to_score", {})
        first_team = {}
        if first_team_raw:
            team_val = first_team_raw.get("team")
            if team_val == home_team_name:
                first_team["team"] = "home"
            elif team_val == away_team_name:
                first_team["team"] = "away"
            else:
                first_team["team"] = team_val
            first_team["probability"] = first_team_raw.get("probability", 0)

        btts = goal_insights.get("both_teams_to_score", {})

        player_prediction = output.get("player_prediction", {})
        player_predictions = []
        clean_sheet_predictions = []
        goal_scorers = {"home": [], "away": []}

        for side in ["home_team", "away_team"]:
            side_data = player_prediction.get(side, {})
            short_side = side.split('_')[0]
            # Goal predictions
            goal_list = side_data.get("goal", [])
            for p in goal_list:
                name = p.get("name")
                preds = p.get("predictions", [])
                
                if not preds:
                    continue
                
                best_pred = max(preds, key=lambda x: x.get("probability", 0))
                predicted_goals = best_pred.get("goal_count", 0)
                goal_prob = best_pred.get("probability", 0)
                
                player_predictions.append({
                    "player_name": name,
                    "team": short_side,
                    "predicted_goals": predicted_goals,
                    "goal_probability": goal_prob
                })
                
                goal_scorers[short_side].append(name)

            # Clean sheet
            cs = side_data.get("clean_sheet_prediction", {})
            if cs and (cs.get("goalkeeper") or cs.get("prediction") is not None):
                clean_sheet_predictions.append(cs)

        payload = {
            "team_id": str(team_id),
            "match_id": str(match_id),
            "submission_id": f"exec_{uuid.uuid4()}",
            "match_prediction": {
                "predicted_winner": winner,
                "predicted_scoreline": {
                    "home_team_goals": home_goals,
                    "away_team_goals": away_goals
                },
                "probabilities": {
                    "home_win_probability": home_prob,
                    "away_win_probability": away_prob,
                    "draw_probability": draw_prob
                },
                "total_goals_prediction": total_goals,
                "first_team_to_score": first_team,
                "both_teams_to_score": btts,
                "clean_sheet_predictions": clean_sheet_predictions,
                "goal_scorers": goal_scorers
            },
            "player_predictions": player_predictions
        }

        return payload