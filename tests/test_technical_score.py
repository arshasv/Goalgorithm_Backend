import json
from pathlib import Path

import pytest

from app.scoring_engine.technical_evaluation.technical_score import (
    calculate_technical_score,
    TechnicalScoreError,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _eval(team_id: str, code: int, backend: int, teamwork: int, ai: int) -> dict:
    return {
        "team_id": team_id,
        "code_quality": code,
        "backend_quality": backend,
        "teamwork": teamwork,
        "ai_explanation": ai,
    }


class TestTechnicalScore:
    def test_perfect_score_gives_20(self):
        result = calculate_technical_score(_eval("TEAM_A", 5, 5, 5, 5))
        assert result["technical_score"] == 20
        assert result["team_id"] == "TEAM_A"

    def test_partial_score_calculation(self):
        result = calculate_technical_score(_eval("TEAM_B", 3, 4, 2, 1))
        assert result["technical_score"] == 10

    def test_zero_in_all_categories(self):
        result = calculate_technical_score(_eval("TEAM_C", 0, 0, 0, 0))
        assert result["technical_score"] == 0

    def test_invalid_negative_code_quality(self):
        with pytest.raises(TechnicalScoreError):
            calculate_technical_score(_eval("TEAM_D", -1, 4, 3, 2))

    def test_invalid_negative_backend_quality(self):
        with pytest.raises(TechnicalScoreError):
            calculate_technical_score(_eval("TEAM_D", 4, -1, 3, 2))

    def test_invalid_negative_teamwork(self):
        with pytest.raises(TechnicalScoreError):
            calculate_technical_score(_eval("TEAM_D", 4, 4, -1, 2))

    def test_invalid_negative_ai_explanation(self):
        with pytest.raises(TechnicalScoreError):
            calculate_technical_score(_eval("TEAM_D", 4, 4, 3, -1))

    def test_invalid_score_above_5(self):
        with pytest.raises(TechnicalScoreError):
            calculate_technical_score(_eval("TEAM_E", 6, 4, 3, 2))

    def test_breakdown_structure(self):
        result = calculate_technical_score(_eval("TEAM_F", 4, 3, 5, 2))
        assert result["breakdown"] == {
            "code_quality": 4,
            "backend_quality": 3,
            "teamwork": 5,
            "ai_explanation": 2,
        }

    def test_loads_from_fixture(self):
        data = json.loads((FIXTURES / "technical_scores.json").read_text())
        for entry in data:
            result = calculate_technical_score(entry)
            assert 0 <= result["technical_score"] <= 20
