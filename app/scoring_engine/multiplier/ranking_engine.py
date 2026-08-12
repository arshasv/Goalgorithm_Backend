def rank_teams(team_scores: list[dict]) -> list[dict]:
    if not team_scores:
        return []

    sorted_teams = sorted(
        team_scores, key=lambda x: x["base_score"], reverse=True
    )

    ranked: list[dict] = []
    current_rank = 1

    for i, team in enumerate(sorted_teams):
        if i > 0 and team["base_score"] < sorted_teams[i - 1]["base_score"]:
            current_rank = i + 1
        ranked.append({
            "team_id": team["team_id"],
            "base_score": team["base_score"],
            "rank": current_rank,
        })

    return ranked
