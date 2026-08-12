PHASE1_MAX = 60
TECHNICAL_MAX = 20
PRESENTATION_MAX = 20
FINAL_MAX = PHASE1_MAX + TECHNICAL_MAX + PRESENTATION_MAX


class LeaderboardError(ValueError):
    pass


def calculate_leaderboard(scores: list[dict]) -> list[dict]:
    if not scores:
        return []

    for entry in scores:
        p1 = entry["phase1_score"]
        tech = entry["technical_score"]
        pres = entry["presentation_score"]

        if p1 < 0 or p1 > PHASE1_MAX:
            raise LeaderboardError(
                f"phase1_score {p1} out of range [0, {PHASE1_MAX}] for {entry['team_id']}"
            )
        if tech < 0 or tech > TECHNICAL_MAX:
            raise LeaderboardError(
                f"technical_score {tech} out of range [0, {TECHNICAL_MAX}] for {entry['team_id']}"
            )
        if pres < 0 or pres > PRESENTATION_MAX:
            raise LeaderboardError(
                f"presentation_score {pres} out of range [0, {PRESENTATION_MAX}] for {entry['team_id']}"
            )

    scored = [
        {
            "team_id": entry["team_id"],
            "scores": {
                "ai_accuracy": entry["phase1_score"],
                "technical": entry["technical_score"],
                "presentation": entry["presentation_score"],
            },
            "final_score": round(
                entry["phase1_score"]
                + entry["technical_score"]
                + entry["presentation_score"],
                2,
            ),
        }
        for entry in scores
    ]

    scored.sort(
        key=lambda x: (
            x["final_score"],
            x["scores"]["ai_accuracy"],
            x["scores"]["technical"],
            x["scores"]["presentation"],
        ),
        reverse=True,
    )

    ranked: list[dict] = []
    current_rank = 1

    for i, entry in enumerate(scored):
        if i > 0:
            prev = scored[i - 1]
            if (
                entry["final_score"] == prev["final_score"]
                and entry["scores"]["ai_accuracy"] == prev["scores"]["ai_accuracy"]
                and entry["scores"]["technical"] == prev["scores"]["technical"]
                and entry["scores"]["presentation"] == prev["scores"]["presentation"]
            ):
                pass
            else:
                current_rank = i + 1

        ranked.append({
            "rank": current_rank,
            "team_id": entry["team_id"],
            "scores": entry["scores"],
            "final_score": entry["final_score"],
        })

    return ranked
