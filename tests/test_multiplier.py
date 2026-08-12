from app.scoring_engine.multiplier.ranking_engine import rank_teams
from app.scoring_engine.multiplier.multiplier_calculator import assign_grades


def _make_team_scores(pairs: list[tuple[str, int]]) -> list[dict]:
    return [
        {"team_id": team_id, "base_score": score}
        for team_id, score in pairs
    ]


class TestRankingEngine:
    def test_five_distinct_scores(self):
        scores = _make_team_scores([
            ("Team A", 23),
            ("Team B", 18),
            ("Team C", 15),
            ("Team D", 12),
            ("Team E", 8),
        ])
        ranked = rank_teams(scores)
        assert ranked[0]["team_id"] == "Team A"
        assert ranked[0]["rank"] == 1
        assert ranked[1]["team_id"] == "Team B"
        assert ranked[1]["rank"] == 2
        assert ranked[2]["team_id"] == "Team C"
        assert ranked[2]["rank"] == 3
        assert ranked[3]["team_id"] == "Team D"
        assert ranked[3]["rank"] == 4
        assert ranked[4]["team_id"] == "Team E"
        assert ranked[4]["rank"] == 5

    def test_tie_at_top(self):
        scores = _make_team_scores([
            ("Team A", 25),
            ("Team B", 25),
            ("Team C", 20),
            ("Team D", 15),
            ("Team E", 10),
        ])
        ranked = rank_teams(scores)
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 1
        assert ranked[2]["rank"] == 3
        assert ranked[3]["rank"] == 4
        assert ranked[4]["rank"] == 5

    def test_tie_at_middle(self):
        scores = _make_team_scores([
            ("Team A", 25),
            ("Team B", 20),
            ("Team C", 20),
            ("Team D", 15),
            ("Team E", 10),
        ])
        ranked = rank_teams(scores)
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 2
        assert ranked[2]["rank"] == 2
        assert ranked[3]["rank"] == 4
        assert ranked[4]["rank"] == 5

    def test_tie_at_bottom(self):
        scores = _make_team_scores([
            ("Team A", 25),
            ("Team B", 20),
            ("Team C", 15),
            ("Team D", 10),
            ("Team E", 10),
        ])
        ranked = rank_teams(scores)
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 2
        assert ranked[2]["rank"] == 3
        assert ranked[3]["rank"] == 4
        assert ranked[4]["rank"] == 4

    def test_all_equal_scores(self):
        scores = _make_team_scores([
            ("Team A", 20),
            ("Team B", 20),
            ("Team C", 20),
            ("Team D", 20),
            ("Team E", 20),
        ])
        ranked = rank_teams(scores)
        for team in ranked:
            assert team["rank"] == 1

    def test_empty_list(self):
        assert rank_teams([]) == []

    def test_preserves_input_order_for_ties(self):
        scores = _make_team_scores([
            ("Team A", 20),
            ("Team B", 20),
            ("Team C", 20),
        ])
        ranked = rank_teams(scores)
        ids = [t["team_id"] for t in ranked]
        assert ids == ["Team A", "Team B", "Team C"]


class TestMultiplierCalculator:
    def test_rank1_gets_A(self):
        ranked = [
            {"team_id": "Team A", "base_score": 23, "rank": 1},
            {"team_id": "Team B", "base_score": 18, "rank": 2},
            {"team_id": "Team C", "base_score": 15, "rank": 3},
            {"team_id": "Team D", "base_score": 12, "rank": 4},
            {"team_id": "Team E", "base_score": 8, "rank": 5},
        ]
        results = assign_grades(ranked)
        assert results[0]["grade"] == "A"
        assert results[0]["multiplier"] == 3
        assert results[0]["earned_points"] == 23 * 3

    def test_rank5_gets_C(self):
        ranked = [
            {"team_id": "Team A", "base_score": 23, "rank": 1},
            {"team_id": "Team B", "base_score": 18, "rank": 2},
            {"team_id": "Team C", "base_score": 15, "rank": 3},
            {"team_id": "Team D", "base_score": 12, "rank": 4},
            {"team_id": "Team E", "base_score": 8, "rank": 5},
        ]
        results = assign_grades(ranked)
        assert results[4]["grade"] == "C"
        assert results[4]["multiplier"] == 1
        assert results[4]["earned_points"] == 8 * 1

    def test_earned_point_calculation(self):
        ranked = [
            {"team_id": "Team A", "base_score": 25, "rank": 1},
            {"team_id": "Team B", "base_score": 10, "rank": 5},
        ]
        results = assign_grades(ranked)
        assert results[0]["earned_points"] == 75
        assert results[1]["earned_points"] == 10

    def test_tie_at_top_both_get_B(self):
        ranked = [
            {"team_id": "Team A", "base_score": 25, "rank": 1},
            {"team_id": "Team B", "base_score": 25, "rank": 1},
            {"team_id": "Team C", "base_score": 20, "rank": 3},
            {"team_id": "Team D", "base_score": 15, "rank": 4},
            {"team_id": "Team E", "base_score": 10, "rank": 5},
        ]
        results = assign_grades(ranked)
        assert results[0]["grade"] == "B"
        assert results[0]["multiplier"] == 2
        assert results[1]["grade"] == "B"
        assert results[1]["multiplier"] == 2
        assert results[2]["grade"] == "B"
        assert results[3]["grade"] == "B"
        assert results[4]["grade"] == "C"

    def test_tie_at_bottom_both_get_C(self):
        ranked = [
            {"team_id": "Team A", "base_score": 25, "rank": 1},
            {"team_id": "Team B", "base_score": 20, "rank": 2},
            {"team_id": "Team C", "base_score": 15, "rank": 3},
            {"team_id": "Team D", "base_score": 10, "rank": 4},
            {"team_id": "Team E", "base_score": 10, "rank": 4},
        ]
        results = assign_grades(ranked)
        assert results[0]["grade"] == "A"
        assert results[3]["grade"] == "C"
        assert results[4]["grade"] == "C"

    def test_all_equal_all_get_B(self):
        ranked = [
            {"team_id": "Team A", "base_score": 20, "rank": 1},
            {"team_id": "Team B", "base_score": 20, "rank": 1},
            {"team_id": "Team C", "base_score": 20, "rank": 1},
            {"team_id": "Team D", "base_score": 20, "rank": 1},
            {"team_id": "Team E", "base_score": 20, "rank": 1},
        ]
        results = assign_grades(ranked)
        for team in results:
            assert team["grade"] == "B"
            assert team["multiplier"] == 2

    def test_full_pipeline_five_teams(self):
        scores = _make_team_scores([
            ("Team A", 23),
            ("Team B", 18),
            ("Team C", 15),
            ("Team D", 12),
            ("Team E", 8),
        ])
        ranked = rank_teams(scores)
        results = assign_grades(ranked)

        assert results[0] == {
            "team_id": "Team A",
            "rank": 1,
            "grade": "A",
            "multiplier": 3,
            "base_score": 23,
            "earned_points": 69,
        }
        assert results[4] == {
            "team_id": "Team E",
            "rank": 5,
            "grade": "C",
            "multiplier": 1,
            "base_score": 8,
            "earned_points": 8,
        }

    def test_empty_list(self):
        assert assign_grades([]) == []
