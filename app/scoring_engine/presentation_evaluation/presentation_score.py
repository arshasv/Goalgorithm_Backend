PHASE3_FIXED_DENOMINATOR = 150
PHASE3_MAX_MARKS = 20

MULTIPLIER_A = 3
MULTIPLIER_B = 2
MULTIPLIER_C = 1

GRADE_A = "A"
GRADE_B = "B"
GRADE_C = "C"


class PresentationScoreError(ValueError):
    pass


def calculate_presentation_scores(
    evaluations: list[dict],
    config: dict | None = None,
) -> list[dict]:
    if not evaluations:
        return []

    criteria_list = []
    if config:
        criteria_list = config.get("presentation_criteria")
    if not criteria_list:
        criteria_list = [
            {"name": "Problem Understanding", "max_score": 10},
            {"name": "Feature Engineering", "max_score": 15},
            {"name": "Team Work", "max_score": 10},
            {"name": "Presentation Quality", "max_score": 10},
            {"name": "Q&A", "max_score": 5}
        ]

    max_marks = sum(item["max_score"] for item in criteria_list)

    scored = []
    for ev in evaluations:
        judge_scores = ev.get("judge_scores", [])
        if judge_scores:
            judge_totals = []
            for j_score in judge_scores:
                if isinstance(j_score, dict) and "scores" in j_score:
                    s_dict = j_score["scores"]
                else:
                    s_dict = j_score
                total = sum(float(val) for val in s_dict.values())
                judge_totals.append(total)
            raw = sum(judge_totals) / len(judge_totals) if judge_totals else 0.0
            judge_count = len(judge_totals)
        else:
            raw = float(ev.get("ai_explanation_score", 0) + ev.get("qa_score", 0) + ev.get("delivery_score", 0))
            judge_count = 0

        scored.append({
            "team_id": ev["team_id"],
            "raw_score": raw,
            "judge_count": judge_count,
            "judge_scores": judge_scores,
        })

    scored.sort(key=lambda x: x["raw_score"], reverse=True)

    ranked: list[dict] = []
    current_rank = 1
    for i, entry in enumerate(scored):
        if i > 0 and entry["raw_score"] < scored[i - 1]["raw_score"]:
            current_rank = i + 1
        ranked.append({
            "team_id": entry["team_id"],
            "raw_score": entry["raw_score"],
            "rank": current_rank,
            "judge_count": entry["judge_count"],
            "judge_scores": entry["judge_scores"],
        })

    num_teams = len(ranked)
    last_rank = ranked[-1]["rank"] if ranked else 1

    results: list[dict] = []
    for entry in ranked:
        rank = entry["rank"]
        score = entry["raw_score"]

        if rank == 1:
            grade, multiplier = GRADE_A, MULTIPLIER_A
        elif rank == last_rank and last_rank > 1:
            grade, multiplier = GRADE_C, MULTIPLIER_C
        else:
            grade, multiplier = GRADE_B, MULTIPLIER_B

        weighted_score = score * multiplier

        results.append({
            "team_id": entry["team_id"],
            "raw_total": round(score, 2),
            "rank": entry["rank"],
            "grade": grade,
            "multiplier": multiplier,
            "weighted_score": round(weighted_score, 2),
            "presentation_score": None,
            "judge_count": entry["judge_count"],
            "judge_scores": entry["judge_scores"],
            "presentation_criteria_config": criteria_list,
            "max_marks": max_marks,
        })

    return results
