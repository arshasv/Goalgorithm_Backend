import pytest

from app.services.leaderboard_service import (
    calculate_leaderboard,
    LeaderboardError,
)


def _entry(team_id, p1, tech, pres):
    return {
        "team_id": team_id,
        "phase1_score": p1,
        "technical_score": tech,
        "presentation_score": pres,
    }


class TestLeaderboard:
    def test_correct_total_calculation(self):
        data = [_entry("TEAM_A", 55, 18, 17)]
        results = calculate_leaderboard(data)
        assert results[0]["final_score"] == 90
        assert results[0]["scores"]["ai_accuracy"] == 55
        assert results[0]["scores"]["technical"] == 18
        assert results[0]["scores"]["presentation"] == 17

    def test_maximum_100_score(self):
        data = [_entry("TEAM_A", 60, 20, 20)]
        results = calculate_leaderboard(data)
        assert results[0]["final_score"] == 100

    def test_ranking_order(self):
        data = [
            _entry("TEAM_A", 55, 18, 17),
            _entry("TEAM_B", 40, 15, 14),
            _entry("TEAM_C", 60, 20, 20),
        ]
        results = calculate_leaderboard(data)
        assert results[0]["team_id"] == "TEAM_C"
        assert results[1]["team_id"] == "TEAM_A"
        assert results[2]["team_id"] == "TEAM_B"
        assert results[0]["rank"] == 1
        assert results[1]["rank"] == 2
        assert results[2]["rank"] == 3

    def test_tie_higher_ai_accuracy_wins(self):
        data = [
            _entry("TEAM_A", 55, 18, 17),
            _entry("TEAM_B", 60, 13, 17),
        ]
        results = calculate_leaderboard(data)
        assert results[0]["team_id"] == "TEAM_B"
        assert results[1]["team_id"] == "TEAM_A"

    def test_tie_ai_accuracy_then_technical(self):
        data = [
            _entry("TEAM_A", 55, 18, 17),
            _entry("TEAM_B", 55, 12, 15),
        ]
        results = calculate_leaderboard(data)
        assert results[0]["team_id"] == "TEAM_A"
        assert results[1]["team_id"] == "TEAM_B"

    def test_tie_ai_and_tech_then_presentation(self):
        data = [
            _entry("TEAM_A", 55, 18, 17),
            _entry("TEAM_B", 55, 18, 10),
        ]
        results = calculate_leaderboard(data)
        assert results[0]["team_id"] == "TEAM_A"
        assert results[1]["team_id"] == "TEAM_B"

    def test_complete_tie_same_rank(self):
        data = [
            _entry("TEAM_A", 55, 18, 17),
            _entry("TEAM_B", 55, 18, 17),
        ]
        results = calculate_leaderboard(data)
        assert results[0]["rank"] == 1
        assert results[1]["rank"] == 1

    def test_three_way_tie_all_same_rank(self):
        data = [
            _entry("TEAM_A", 50, 15, 15),
            _entry("TEAM_B", 50, 15, 15),
            _entry("TEAM_C", 50, 15, 15),
        ]
        results = calculate_leaderboard(data)
        assert all(r["rank"] == 1 for r in results)

    def test_tie_and_distinct_teams(self):
        data = [
            _entry("TEAM_A", 55, 18, 17),
            _entry("TEAM_B", 55, 18, 17),
            _entry("TEAM_C", 50, 15, 15),
        ]
        results = calculate_leaderboard(data)
        assert results[0]["rank"] == 1
        assert results[1]["rank"] == 1
        assert results[2]["rank"] == 3

    def test_output_structure(self):
        data = [_entry("TEAM_A", 50, 15, 15)]
        results = calculate_leaderboard(data)
        r = results[0]
        assert set(r.keys()) == {"rank", "team_id", "scores", "final_score"}
        assert set(r["scores"].keys()) == {"ai_accuracy", "technical", "presentation"}

    def test_rounding_two_decimals(self):
        data = [_entry("TEAM_A", 33.33, 16.67, 14.0)]
        results = calculate_leaderboard(data)
        assert results[0]["final_score"] == 64.0

    def test_empty_input(self):
        assert calculate_leaderboard([]) == []

    def test_negative_phase1_raises_error(self):
        data = [_entry("TEAM_A", -5, 15, 15)]
        with pytest.raises(LeaderboardError):
            calculate_leaderboard(data)

    def test_phase1_exceeds_max_raises_error(self):
        data = [_entry("TEAM_A", 61, 15, 15)]
        with pytest.raises(LeaderboardError):
            calculate_leaderboard(data)

    def test_technical_exceeds_max_raises_error(self):
        data = [_entry("TEAM_A", 50, 21, 15)]
        with pytest.raises(LeaderboardError):
            calculate_leaderboard(data)

    def test_presentation_exceeds_max_raises_error(self):
        data = [_entry("TEAM_A", 50, 15, 21)]
        with pytest.raises(LeaderboardError):
            calculate_leaderboard(data)

    def test_example_from_docstring(self):
        data = [_entry("TEAM_A", 55, 18, 17)]
        results = calculate_leaderboard(data)
        assert results[0]["final_score"] == 90
        assert results[0]["scores"]["ai_accuracy"] == 55
        assert results[0]["scores"]["technical"] == 18
        assert results[0]["scores"]["presentation"] == 17

    def test_five_team_leaderboard(self):
        data = [
            _entry("TEAM_A", 55, 18, 17),
            _entry("TEAM_B", 50, 16, 15),
            _entry("TEAM_C", 60, 20, 20),
            _entry("TEAM_D", 30, 10, 10),
            _entry("TEAM_E", 45, 14, 13),
        ]
        results = calculate_leaderboard(data)
        assert results[0]["team_id"] == "TEAM_C"
        assert results[0]["final_score"] == 100
        assert results[-1]["team_id"] == "TEAM_D"
        assert results[-1]["final_score"] == 50
