import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.prediction_schema import PredictionSubmission
from app.schemas.actual_result_schema import ActualResultSubmission
from app.schemas.technical_evaluation_schema import TechnicalEvaluation
from app.schemas.presentation_schema import PresentationEvaluation

FIXTURES = Path(__file__).parent / "fixtures"


class TestPredictionSchema:
    def test_valid_prediction_passes(self):
        data = json.loads((FIXTURES / "valid_prediction.json").read_text())
        model = PredictionSubmission(**data)
        assert model.team_id == "team-001"
        assert model.match_prediction.predicted_winner == "home"
        assert len(model.player_predictions) == 2

    def test_five_team_predictions_all_valid(self):
        data = json.loads((FIXTURES / "five_team_predictions.json").read_text())
        assert len(data) == 5
        team_ids = set()
        for entry in data:
            model = PredictionSubmission(**entry)
            team_ids.add(model.team_id)
            assert model.match_id == "match-001"
            assert len(model.player_predictions) >= 3
        assert team_ids == {"Team A", "Team B", "Team C", "Team D", "Team E"}

    def test_five_team_predictions_have_diverse_winners(self):
        data = json.loads((FIXTURES / "five_team_predictions.json").read_text())
        winners = {entry["match_prediction"]["predicted_winner"] for entry in data}
        assert len(winners) > 1

    def test_invalid_prediction_fails(self):
        data = json.loads((FIXTURES / "invalid_prediction.json").read_text())
        with pytest.raises(ValidationError):
            PredictionSubmission(**data)

    def test_empty_team_id_fails(self):
        data = {
            "team_id": "",
            "match_id": "m-1",
            "submission_id": "s-1",
            "match_prediction": {
                "predicted_winner": "home",
                "predicted_scoreline": {"home_team_goals": 1, "away_team_goals": 0},
                "probabilities": {
                    "home_win_probability": 50.0,
                    "draw_probability": 30.0,
                    "away_win_probability": 20.0,
                },
                "clean_sheet_probability": {"home_team": 30.0, "away_team": 20.0},
                "first_goal_team": "home",
                "both_teams_to_score_probability": 50.0,
                "total_goals_prediction": 1,
            },
            "player_predictions": [
                {
                    "player_id": "p-1",
                    "player_name": "Player",
                    "goal_probability": 30.0,
                    "predicted_goals": 1,
                    "assist_probability": 10.0,
                }
            ],
        }
        with pytest.raises(ValidationError):
            PredictionSubmission(**data)

    def test_negative_goals_fails(self):
        data = {
            "team_id": "t-1",
            "match_id": "m-1",
            "submission_id": "s-1",
            "match_prediction": {
                "predicted_winner": "home",
                "predicted_scoreline": {"home_team_goals": -1, "away_team_goals": 0},
                "probabilities": {
                    "home_win_probability": 50.0,
                    "draw_probability": 30.0,
                    "away_win_probability": 20.0,
                },
                "clean_sheet_probability": {"home_team": 30.0, "away_team": 20.0},
                "first_goal_team": "home",
                "both_teams_to_score_probability": 50.0,
                "total_goals_prediction": 1,
            },
            "player_predictions": [
                {
                    "player_id": "p-1",
                    "player_name": "Player",
                    "goal_probability": 30.0,
                    "predicted_goals": 1,
                    "assist_probability": 10.0,
                }
            ],
        }
        with pytest.raises(ValidationError):
            PredictionSubmission(**data)

    def test_invalid_winner_fails(self):
        data = {
            "team_id": "t-1",
            "match_id": "m-1",
            "submission_id": "s-1",
            "match_prediction": {
                "predicted_winner": "invalid",
                "predicted_scoreline": {"home_team_goals": 1, "away_team_goals": 0},
                "probabilities": {
                    "home_win_probability": 50.0,
                    "draw_probability": 30.0,
                    "away_win_probability": 20.0,
                },
                "clean_sheet_probability": {"home_team": 30.0, "away_team": 20.0},
                "first_goal_team": "home",
                "both_teams_to_score_probability": 50.0,
                "total_goals_prediction": 1,
            },
            "player_predictions": [
                {
                    "player_id": "p-1",
                    "player_name": "Player",
                    "goal_probability": 30.0,
                    "predicted_goals": 1,
                    "assist_probability": 10.0,
                }
            ],
        }
        with pytest.raises(ValidationError):
            PredictionSubmission(**data)

    def test_probability_out_of_range_fails(self):
        data = {
            "team_id": "t-1",
            "match_id": "m-1",
            "submission_id": "s-1",
            "match_prediction": {
                "predicted_winner": "home",
                "predicted_scoreline": {"home_team_goals": 1, "away_team_goals": 0},
                "probabilities": {
                    "home_win_probability": 150.0,
                    "draw_probability": 30.0,
                    "away_win_probability": 20.0,
                },
                "clean_sheet_probability": {"home_team": 30.0, "away_team": 20.0},
                "first_goal_team": "home",
                "both_teams_to_score_probability": 50.0,
                "total_goals_prediction": 1,
            },
            "player_predictions": [
                {
                    "player_id": "p-1",
                    "player_name": "Player",
                    "goal_probability": 30.0,
                    "predicted_goals": 1,
                    "assist_probability": 10.0,
                }
            ],
        }
        with pytest.raises(ValidationError):
            PredictionSubmission(**data)

    def test_empty_player_list_is_valid(self):
        """Empty player_predictions is now valid (AI format may omit players)."""
        data = {
            "team_id": "t-1",
            "match_id": "m-1",
            "submission_id": "s-1",
            "match_prediction": {
                "predicted_winner": "home",
                "predicted_scoreline": {"home_team_goals": 1, "away_team_goals": 0},
                "probabilities": {
                    "home_win_probability": 50.0,
                    "draw_probability": 30.0,
                    "away_win_probability": 20.0,
                },
                "clean_sheet_probability": {"home_team": 30.0, "away_team": 20.0},
                "first_goal_team": "home",
                "both_teams_to_score_probability": 50.0,
                "total_goals_prediction": 1,
            },
            "player_predictions": [],
        }
        model = PredictionSubmission(**data)
        assert len(model.player_predictions) == 0

    def test_missing_player_predictions_defaults_empty(self):
        """player_predictions now defaults to empty list when omitted."""
        data = {
            "team_id": "t-1",
            "match_id": "m-1",
            "submission_id": "s-1",
            "match_prediction": {
                "predicted_winner": "home",
                "predicted_scoreline": {"home_team_goals": 1, "away_team_goals": 0},
                "probabilities": {
                    "home_win_probability": 50.0,
                    "draw_probability": 30.0,
                    "away_win_probability": 20.0,
                },
                "clean_sheet_probability": {"home_team": 30.0, "away_team": 20.0},
                "first_goal_team": "home",
                "both_teams_to_score_probability": 50.0,
                "total_goals_prediction": 1,
            },
        }
        model = PredictionSubmission(**data)
        assert len(model.player_predictions) == 0

    def test_ai_format_auto_calculates_winner(self):
        """predicted_winner should be auto-calculated from highest probability."""
        data = {
            "team_id": "t-1",
            "match_id": "m-1",
            "submission_id": "s-1",
            "match_prediction": {
                "predicted_scoreline": {"home_team_goals": 2, "away_team_goals": 1},
                "probabilities": {
                    "home_win_probability": 48.0,
                    "draw_probability": 25.0,
                    "away_win_probability": 27.0,
                },
                "both_teams_to_score": {"prediction": True, "probability": 62.5},
                "first_team_to_score": {"team": "home", "probability": 55.0},
            },
            "player_predictions": [
                {"player_name": "Messi", "team": "Argentina", "predicted_goals": 1, "probability": 45.5}
            ],
        }
        model = PredictionSubmission(**data)
        assert model.match_prediction.predicted_winner == "home"
        assert model.match_prediction.total_goals_prediction == 3
        assert model.player_predictions[0].team == "Argentina"


class TestActualResultSchema:
    def test_valid_actual_result_passes(self):
        data = json.loads((FIXTURES / "actual_result.json").read_text())
        model = ActualResultSubmission(**data)
        assert str(model.match_id) == "00000000-0000-0000-0000-000000000001"
        assert model.actual_winner == "home"

    def test_negative_goals_fails(self):
        data = {
            "match_id": "m-1",
            "actual_winner": "home",
            "final_score": {"home_team_goals": -1, "away_team_goals": 0},
            "player_results": [
                {"player_id": "p-1", "player_name": "Player", "actual_goals": 1}
            ],
        }
        with pytest.raises(ValidationError):
            ActualResultSubmission(**data)

    def test_empty_match_id_fails(self):
        data = {
            "match_id": "",
            "actual_winner": "home",
            "final_score": {"home_team_goals": 1, "away_team_goals": 0},
            "player_results": [
                {"player_id": "p-1", "player_name": "Player", "actual_goals": 1}
            ],
        }
        with pytest.raises(ValidationError):
            ActualResultSubmission(**data)

    def test_invalid_winner_fails(self):
        data = {
            "match_id": "00000000-0000-0000-0000-000000000001",
            "actual_winner": "invalid",
            "final_score": {"home_team_goals": 1, "away_team_goals": 0},
            "player_results": [
                {"player_id": "p-1", "player_name": "Player", "actual_goals": 1}
            ],
        }
        with pytest.raises(ValidationError):
            ActualResultSubmission(**data)

    def test_empty_player_list_fails(self):
        data = {
            "match_id": "00000000-0000-0000-0000-000000000001",
            "actual_winner": "home",
            "final_score": {"home_team_goals": 1, "away_team_goals": 0},
            "player_results": [],
        }
        with pytest.raises(ValidationError):
            ActualResultSubmission(**data)


class TestTechnicalEvaluationSchema:
    def test_valid_technical_evaluation_passes(self):
        data = {
            "team_id": "team-001",
            "code_quality": 4,
            "backend_quality": 5,
            "teamwork": 3,
            "ai_explanation": 4,
        }
        model = TechnicalEvaluation(**data)
        assert model.team_id == "team-001"

    def test_technical_scores_fixture_all_valid(self):
        data = json.loads((FIXTURES / "technical_scores.json").read_text())
        assert len(data) == 5
        team_ids = set()
        for entry in data:
            model = TechnicalEvaluation(**entry)
            team_ids.add(model.team_id)
        assert team_ids == {"Team A", "Team B", "Team C", "Team D", "Team E"}

    def test_score_above_max_fails(self):
        data = {
            "team_id": "team-001",
            "code_quality": 6,
            "backend_quality": 5,
            "teamwork": 3,
            "ai_explanation": 4,
        }
        with pytest.raises(ValidationError):
            TechnicalEvaluation(**data)

    def test_negative_score_fails(self):
        data = {
            "team_id": "team-001",
            "code_quality": -1,
            "backend_quality": 5,
            "teamwork": 3,
            "ai_explanation": 4,
        }
        with pytest.raises(ValidationError):
            TechnicalEvaluation(**data)

    def test_missing_team_id_fails(self):
        data = {
            "code_quality": 4,
            "backend_quality": 5,
            "teamwork": 3,
            "ai_explanation": 4,
        }
        with pytest.raises(ValidationError):
            TechnicalEvaluation(**data)


class TestPresentationSchema:
    def test_valid_presentation_passes(self):
        data = {
            "team_id": "team-001",
            "judge_scores": [
                {
                    "Problem Understanding": 8.0,
                    "Feature Engineering": 12.0,
                }
            ],
        }
        model = PresentationEvaluation(**data)
        assert model.team_id == "team-001"
        assert len(model.judge_scores) == 1

    def test_empty_team_id_fails(self):
        data = {
            "team_id": "",
            "judge_scores": [],
        }
        with pytest.raises(ValidationError):
            PresentationEvaluation(**data)

