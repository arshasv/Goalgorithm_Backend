WINNER_CORRECT = 2.5
WINNER_INCORRECT = 0.0
FIRST_TEAM_CORRECT = 2.5
FIRST_TEAM_INCORRECT = 0.0
MAX_WINNER_SCORE = 5.0


def calculate_winner_score(
    prediction: dict,
    actual_result: dict,
    config: dict | None = None,
) -> float:
    mp = prediction["match_prediction"]
    predicted_winner = mp.get("predicted_winner")
    actual_winner = actual_result.get("actual_winner")

    if predicted_winner == actual_winner:
        winner_points = WINNER_CORRECT
    else:
        winner_points = WINNER_INCORRECT

    pred_first_team = None
    if mp.get("first_team_to_score") is not None:
        pred_first_team = mp["first_team_to_score"]["team"].lower()
    elif mp.get("first_goal_team") is not None:
        pred_first_team = mp["first_goal_team"].lower()

    actual_first = actual_result.get("first_team_to_score", "none").lower()

    if pred_first_team is not None and pred_first_team == actual_first:
        first_team_points = FIRST_TEAM_CORRECT
    else:
        first_team_points = FIRST_TEAM_INCORRECT

    total = winner_points + first_team_points
    return min(total, MAX_WINNER_SCORE)
