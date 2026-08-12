TECHNICAL_MAX_PER_CATEGORY = 5
TECHNICAL_MAX_TOTAL = 20


class TechnicalScoreError(ValueError):
    pass


def _validate_score(value: int, label: str, max_per_cat: int) -> None:
    if value < 0:
        raise TechnicalScoreError(f"{label} cannot be negative: {value}")
    if value > max_per_cat:
        raise TechnicalScoreError(
            f"{label} exceeds max {max_per_cat}: {value}"
        )


def calculate_technical_score(
    evaluation: dict,
    config: dict | None = None,
) -> dict:
    max_per_cat = config.get("technical_max_per_category", TECHNICAL_MAX_PER_CATEGORY) if config else TECHNICAL_MAX_PER_CATEGORY
    max_total = config.get("technical_max_total", TECHNICAL_MAX_TOTAL) if config else TECHNICAL_MAX_TOTAL

    code_quality = evaluation["code_quality"]
    backend_quality = evaluation["backend_quality"]
    teamwork = evaluation["teamwork"]
    ai_explanation = evaluation["ai_explanation"]

    _validate_score(code_quality, "code_quality", max_per_cat)
    _validate_score(backend_quality, "backend_quality", max_per_cat)
    _validate_score(teamwork, "teamwork", max_per_cat)
    _validate_score(ai_explanation, "ai_explanation", max_per_cat)

    total = code_quality + backend_quality + teamwork + ai_explanation
    capped = min(total, max_total)

    return {
        "team_id": evaluation["team_id"],
        "breakdown": {
            "code_quality": code_quality,
            "backend_quality": backend_quality,
            "teamwork": teamwork,
            "ai_explanation": ai_explanation,
        },
        "technical_score": capped,
    }
