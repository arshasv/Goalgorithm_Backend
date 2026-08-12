import json
from pathlib import Path

from app.scoring_engine.base_score.winner_score import calculate_winner_score
from app.scoring_engine.base_score.scoreline_score import calculate_scoreline_score
from app.scoring_engine.base_score.probability_score import calculate_probability_score
from app.scoring_engine.base_score.player_score import calculate_player_score
from app.scoring_engine.base_score.base_score_calculator import calculate_base_score

FIXTURES = Path(__file__).parent / "fixtures"
ACTUAL = json.loads((FIXTURES / "actual_result.json").read_text())

# Actual Argentina 2-0 Brazil
ACTUAL_PROBS = {
    "home_win_probability": 60.0,
    "draw_probability": 25.0,
    "away_win_probability": 15.0,
    "home_clean_sheet_probability": 55.0,
    "away_clean_sheet_probability": 10.0,
}


def _team_prediction(team_id: str) -> dict:
    data = json.loads((FIXTURES / "five_team_predictions.json").read_text())
    for entry in data:
        if entry["team_id"] == team_id:
            return entry
    raise ValueError(f"Team {team_id} not found")


class TestWinnerScore:
    def test_correct_winner_home(self):
        pred = _team_prediction("Team A")
        assert calculate_winner_score(pred, ACTUAL) == 5

    def test_incorrect_winner(self):
        pred = _team_prediction("Team E")
        assert calculate_winner_score(pred, ACTUAL) == 0

    def test_incorrect_winner_draw(self):
        pred = _team_prediction("Team D")
        assert calculate_winner_score(pred, ACTUAL) == 0


class TestScorelineScore:
    def test_exact_scoreline(self):
        pred = _team_prediction("Team A")
        assert calculate_scoreline_score(pred, ACTUAL) == 10

    def test_correct_goal_margin(self):
        pred = {
            "match_prediction": {
                "predicted_scoreline": {"home_team_goals": 3, "away_team_goals": 1},
            },
        }
        assert calculate_scoreline_score(pred, ACTUAL) == 5

    def test_zero_goal_margin_draw_prediction(self):
        actual_draw = {
            "actual_winner": "draw",
            "final_score": {"home_team_goals": 1, "away_team_goals": 1},
        }
        pred = {
            "match_prediction": {
                "predicted_scoreline": {"home_team_goals": 2, "away_team_goals": 2},
            },
        }
        assert calculate_scoreline_score(pred, actual_draw) == 5



class TestBaseScoreCalculator:
    def test_scoreline_priority_1_exact(self):
        # TEST 1: Prediction: 2-1, Actual: 2-1 -> Expected: 10
        pred = {
            "match_prediction": {
                "predicted_scoreline": {"home_team_goals": 2, "away_team_goals": 1}
            }
        }
        actual = {
            "final_score": {"home_team_goals": 2, "away_team_goals": 1}
        }
        assert calculate_scoreline_score(pred, actual) == 10.0

    def test_scoreline_priority_2_difference(self):
        # TEST 2: Prediction: 2-1, Actual: 3-2 -> Expected: 5
        pred = {
            "match_prediction": {
                "predicted_scoreline": {"home_team_goals": 2, "away_team_goals": 1}
            }
        }
        actual = {
            "final_score": {"home_team_goals": 3, "away_team_goals": 2}
        }
        assert calculate_scoreline_score(pred, actual) == 5.0

    def test_scoreline_priority_3_partial(self):
        # TEST 3: Prediction: 2-1, Actual: 2-0 -> Expected: 2.5
        pred = {
            "match_prediction": {
                "predicted_scoreline": {"home_team_goals": 2, "away_team_goals": 1}
            }
        }
        actual = {
            "final_score": {"home_team_goals": 2, "away_team_goals": 0}
        }
        assert calculate_scoreline_score(pred, actual) == 2.5

    def test_scoreline_priority_3_partial_away(self):
        pred = {
            "match_prediction": {
                "predicted_scoreline": {"home_team_goals": 1, "away_team_goals": 2}
            }
        }
        actual = {
            "final_score": {"home_team_goals": 3, "away_team_goals": 2}
        }
        assert calculate_scoreline_score(pred, actual) == 2.5

    def test_perfect_prediction_25(self):
        pred = {
            "team_id": "Team A",
            "match_id": "match-001",
            "match_prediction": {
                "predicted_winner": "home",
                "predicted_scoreline": {"home_team_goals": 2, "away_team_goals": 1},
                "probabilities": {
                    "home_win_probability": 75.0,
                    "draw_probability": 15.0,
                    "away_win_probability": 10.0,
                },
                "both_teams_to_score": {"prediction": True},
                "clean_sheet_predictions": [
                    {"prediction": False},
                    {"prediction": False}
                ]
            },
            "player_predictions": [
                {"player_name": "Messi", "predicted_goals": 1}
            ]
        }
        actual = {
            "actual_winner": "home",
            "final_score": {"home_team_goals": 2, "away_team_goals": 1},
            "player_results": [
                {"player_name": "Messi", "actual_goals": 1}
            ]
        }
        result = calculate_base_score(pred, actual)
        assert result["base_score"] == 25.0
        assert result["breakdown"]["winner_score"] == 5.0
        assert result["breakdown"]["scoreline_score"] == 10.0
        assert result["breakdown"]["probability_score"] == 5.0
        assert result["breakdown"]["player_score"] == 5.0

    def test_probability_score_logic(self):
        # actual is 1-0, home wins, home clean sheet (away 0), away no clean sheet (home 1)
        actual = {
            "actual_winner": "home",
            "final_score": {"home_team_goals": 1, "away_team_goals": 0},
        }
        
        # Test confidence: 55% -> 1.5, BTTS -> false (match = 1), Clean sheet: home true (match = 1), away false (match = 1) -> Total = 4.5
        pred = {
            "match_prediction": {
                "predicted_winner": "home",
                "probabilities": {"home_win_probability": 55.0},
                "both_teams_to_score": {"prediction": False},
                "clean_sheet_predictions": [
                    {"prediction": True},
                    {"prediction": False}
                ]
            }
        }
        assert calculate_probability_score(pred, actual) == 4.5

    def test_player_score_best_match(self):
        # Best match takes max score
        pred = {
            "player_predictions": [
                {"player_name": "Messi", "predicted_goals": 1}, # diff 1 => 2 pts
                {"player_name": "Alvarez", "predicted_goals": 2} # exact => 5 pts
            ]
        }
        actual = {
            "player_results": [
                {"player_name": "Messi", "actual_goals": 2},
                {"player_name": "Alvarez", "actual_goals": 2}
            ]
        }
        assert calculate_player_score(pred, actual) == 5.0

