import pytest
from app.scoring_engine.presentation_evaluation.presentation_score import (
    calculate_presentation_scores,
    PresentationScoreError,
)


class TestPresentationScore:
    def test_single_judge_default_criteria(self):
        evals = [
            {
                "team_id": "TEAM_A",
                "judge_scores": [
                    {
                        "Problem Understanding": 8,
                        "Feature Engineering": 12,
                        "Team Work": 9,
                        "Presentation Quality": 8,
                        "Q&A": 4,
                    }
                ],
            }
        ]
        results = calculate_presentation_scores(evals)
        assert len(results) == 1
        assert results[0]["raw_total"] == 41.0
        assert results[0]["presentation_score"] is None
        assert results[0]["judge_count"] == 1
        assert results[0]["max_marks"] == 50
        assert results[0]["rank"] == 1
        assert results[0]["grade"] == "A"
        assert results[0]["multiplier"] == 3
        assert results[0]["weighted_score"] == 123.0  # 41.0 * 3

    def test_multiple_judges_average(self):
        evals = [
            {
                "team_id": "TEAM_A",
                "judge_scores": [
                    {
                        "Problem Understanding": 8,
                        "Feature Engineering": 12,
                        "Team Work": 9,
                        "Presentation Quality": 8,
                        "Q&A": 4,
                    },  # Total = 41
                    {
                        "Problem Understanding": 9,
                        "Feature Engineering": 13,
                        "Team Work": 10,
                        "Presentation Quality": 9,
                        "Q&A": 4,
                    },  # Total = 45
                ],
            }
        ]
        results = calculate_presentation_scores(evals)
        assert len(results) == 1
        assert results[0]["raw_total"] == 43.0  # (41 + 45) / 2
        assert results[0]["presentation_score"] is None
        assert results[0]["judge_count"] == 2
        assert results[0]["max_marks"] == 50
        assert results[0]["grade"] == "A"
        assert results[0]["multiplier"] == 3
        assert results[0]["weighted_score"] == 129.0  # 43.0 * 3

    def test_rank_assignment_based_on_average(self):
        evals = [
            {
                "team_id": "TEAM_A",
                "judge_scores": [
                    {"c1": 10, "c2": 15},  # Total = 25
                    {"c1": 8, "c2": 12},   # Total = 20
                ],  # Average = 22.5
            },
            {
                "team_id": "TEAM_B",
                "judge_scores": [
                    {"c1": 10, "c2": 20},  # Total = 30
                    {"c1": 10, "c2": 18},  # Total = 28
                ],  # Average = 29.0
            },
        ]
        config = {
            "presentation_criteria": [
                {"name": "c1", "max_score": 10},
                {"name": "c2", "max_score": 20},
            ]
        }
        results = calculate_presentation_scores(evals, config)
        assert len(results) == 2
        # TEAM_B should be rank 1
        assert results[0]["team_id"] == "TEAM_B"
        assert results[0]["rank"] == 1
        assert results[0]["presentation_score"] is None
        assert results[0]["grade"] == "A"
        assert results[0]["multiplier"] == 3
        assert results[0]["weighted_score"] == 87.0  # 29.0 * 3

        # TEAM_A should be rank 2 (last rank → Grade C ×1)
        assert results[1]["team_id"] == "TEAM_A"
        assert results[1]["rank"] == 2
        assert results[1]["presentation_score"] is None
        assert results[1]["grade"] == "C"
        assert results[1]["multiplier"] == 1
        assert results[1]["weighted_score"] == 22.5  # 22.5 * 1

    def test_empty_input(self):
        assert calculate_presentation_scores([]) == []

    def test_output_structure(self):
        evals = [
            {
                "team_id": "TEAM_A",
                "judge_scores": [{"c1": 5}],
            }
        ]
        results = calculate_presentation_scores(evals)
        assert len(results) == 1
        assert set(results[0].keys()) == {
            "team_id",
            "judge_count",
            "judge_scores",
            "presentation_criteria_config",
            "max_marks",
            "raw_total",
            "presentation_score",
            "rank",
            "grade",
            "multiplier",
            "weighted_score",
        }
