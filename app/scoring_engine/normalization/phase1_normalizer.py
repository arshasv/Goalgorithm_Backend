MAX_BASE_SCORE = 25
BEST_MULTIPLIER = 3
MAX_EARNED_PER_MATCH = MAX_BASE_SCORE * BEST_MULTIPLIER  # 75
PHASE1_MAX_MARKS = 60


class NormalizationError(ValueError):
    pass


def calculate_phase1_score(
    team_data: dict,
    config: dict | None = None,
) -> dict:
    max_base = config.get("max_base_score", MAX_BASE_SCORE) if config else MAX_BASE_SCORE
    best_mult = config.get("multiplier_a", BEST_MULTIPLIER) if config else BEST_MULTIPLIER
    max_earned_per_match = max_base * best_mult
    phase1_max = config.get("phase1_max_marks", PHASE1_MAX_MARKS) if config else PHASE1_MAX_MARKS

    matches = team_data.get("matches", [])
    if not matches:
        return {
            "team_id": team_data["team_id"],
            "total_earned_points": 0,
            "matches_played": 0,
            "phase1_score": 0.0,
        }

    for m in matches:
        pts = m["earned_points"]
        if pts < 0:
            raise NormalizationError(
                f"match {m['match_id']} has negative earned_points: {pts}"
            )

    total_earned = sum(m["earned_points"] for m in matches)
    matches_played = len(matches)
    maximum_possible = matches_played * max_earned_per_match

    if total_earned > maximum_possible:
        raise NormalizationError(
            f"total_earned_points {total_earned} exceeds maximum_possible {maximum_possible}"
        )

    phase1_score = round((total_earned / maximum_possible) * phase1_max, 2)

    return {
        "team_id": team_data["team_id"],
        "total_earned_points": total_earned,
        "matches_played": matches_played,
        "phase1_score": phase1_score,
    }
