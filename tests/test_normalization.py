import pytest

from app.scoring_engine.normalization.phase1_normalizer import (
    calculate_phase1_score,
    NormalizationError,
)


def _team_data(team_id: str, match_earned: list[int]) -> dict:
    return {
        "team_id": team_id,
        "matches": [
            {"match_id": f"MATCH_{i:03d}", "earned_points": pts}
            for i, pts in enumerate(match_earned, start=1)
        ],
    }


class TestPhase1Normalization:
    def test_max_score_60(self):
        data = _team_data("Team A", [75] * 32)
        result = calculate_phase1_score(data)
        assert result["team_id"] == "Team A"
        assert result["total_earned_points"] == 2400
        assert result["matches_played"] == 32
        assert result["phase1_score"] == 60.0

    def test_zero_earned_gives_0(self):
        data = _team_data("Team B", [0] * 32)
        result = calculate_phase1_score(data)
        assert result["phase1_score"] == 0.0

    def test_half_earned_gives_30(self):
        data = _team_data("Team C", [75, 75])
        result = calculate_phase1_score(data)
        assert result["total_earned_points"] == 150
        assert result["matches_played"] == 2
        assert result["phase1_score"] == 60.0

    def test_partial_tournament_30(self):
        data = _team_data("Team D", [37] * 32)
        result = calculate_phase1_score(data)
        assert result["phase1_score"] == 29.6

    def test_single_match(self):
        data = _team_data("Team E", [50])
        result = calculate_phase1_score(data)
        assert result["matches_played"] == 1
        assert result["total_earned_points"] == 50
        assert result["phase1_score"] == 40.0

    def test_no_matches_returns_zero(self):
        data = {"team_id": "Team Empty", "matches": []}
        result = calculate_phase1_score(data)
        assert result["phase1_score"] == 0.0
        assert result["total_earned_points"] == 0
        assert result["matches_played"] == 0

    def test_negative_points_raises_error(self):
        data = _team_data("Team Bad", [75, -10])
        with pytest.raises(NormalizationError):
            calculate_phase1_score(data)

    def test_earned_exceeds_maximum_raises_error(self):
        data = _team_data("Team Cheat", [80])
        with pytest.raises(NormalizationError):
            calculate_phase1_score(data)

    def test_precision_two_decimal_places(self):
        data = _team_data("Team Precise", [33] * 5)
        result = calculate_phase1_score(data)
        score_str = str(result["phase1_score"])
        if "." in score_str:
            decimals = len(score_str.split(".")[1])
            assert decimals <= 2

    def test_mixed_match_scores(self):
        data = _team_data("Team Mixed", [75, 50, 25, 0])
        result = calculate_phase1_score(data)
        assert result["total_earned_points"] == 150
        assert result["matches_played"] == 4
        assert result["phase1_score"] == 30.0

    def test_output_structure(self):
        data = _team_data("Team Output", [60, 45])
        result = calculate_phase1_score(data)
        assert set(result.keys()) == {
            "team_id",
            "total_earned_points",
            "matches_played",
            "phase1_score",
        }
