MULTIPLIER_A = 3
MULTIPLIER_B = 2
MULTIPLIER_C = 1

GRADE_A = "A"
GRADE_B = "B"
GRADE_C = "C"


def assign_grades(
    ranked_teams: list[dict],
    config: dict | None = None,
) -> list[dict]:
    if not ranked_teams:
        return []

    mult_a = config.get("multiplier_a", MULTIPLIER_A) if config else MULTIPLIER_A
    mult_b = config.get("multiplier_b", MULTIPLIER_B) if config else MULTIPLIER_B
    mult_c = config.get("multiplier_c", MULTIPLIER_C) if config else MULTIPLIER_C

    scores = [t["base_score"] for t in ranked_teams]
    highest = max(scores)
    lowest = min(scores)

    results: list[dict] = []
    for team in ranked_teams:
        score = team["base_score"]

        if score == highest:
            grade, multiplier = GRADE_A, mult_a
        elif score == lowest:
            grade, multiplier = GRADE_C, mult_c
        else:
            grade, multiplier = GRADE_B, mult_b

        earned_points = score * multiplier

        results.append({
            "team_id": team["team_id"],
            "rank": team["rank"],
            "grade": grade,
            "multiplier": multiplier,
            "base_score": score,
            "earned_points": earned_points,
        })

    return results
