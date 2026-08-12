import json
from pathlib import Path

from app.schemas.prediction_schema import PredictionSubmission
from app.schemas.actual_result_schema import ActualResultSubmission
from app.schemas.technical_evaluation_schema import TechnicalEvaluation
from app.schemas.presentation_schema import PresentationEvaluation
from app.scoring_engine.base_score.base_score_calculator import calculate_base_score
from app.scoring_engine.multiplier.ranking_engine import rank_teams
from app.scoring_engine.multiplier.multiplier_calculator import assign_grades
from app.scoring_engine.normalization.phase1_normalizer import calculate_phase1_score
from app.scoring_engine.technical_evaluation.technical_score import (
    calculate_technical_score,
)
from app.scoring_engine.presentation_evaluation.presentation_score import (
    calculate_presentation_scores,
)
from app.services.leaderboard_service import calculate_leaderboard

FIXTURES = Path(__file__).parent / "fixtures"

ACTUAL = json.loads((FIXTURES / "actual_result.json").read_text())

ACTUAL_PROBS = {
    "home_win_probability": 60.0,
    "draw_probability": 25.0,
    "away_win_probability": 15.0,
    "home_clean_sheet_probability": 55.0,
    "away_clean_sheet_probability": 10.0,
}

TEAM_IDS = ["Team A", "Team B", "Team C", "Team D", "Team E"]


def _load_predictions() -> list[dict]:
    return json.loads((FIXTURES / "five_team_predictions.json").read_text())


def _load_technical() -> list[dict]:
    return json.loads((FIXTURES / "technical_scores.json").read_text())


def _load_presentation() -> list[dict]:
    return json.loads((FIXTURES / "presentation_scores.json").read_text())


class TestFullCompetitionFlow:
    def test_full_competition_flow(self):
        # 1. Load team predictions
        predictions = _load_predictions()
        assert len(predictions) == 5

        # 2. Validate using schemas
        validated = []
        for pred in predictions:
            submission = PredictionSubmission(**pred)
            validated.append(submission.model_dump())

        assert len(validated) == 5
        team_ids = {v["team_id"] for v in validated}
        assert team_ids == set(TEAM_IDS)

        # 3. Calculate base score /25 for each team
        base_results = {}
        for pred in validated:
            result = calculate_base_score(pred, ACTUAL, ACTUAL_PROBS)
            base_results[result["team_id"]] = result["base_score"]

        assert len(base_results) == 5
        for tid, score in base_results.items():
            assert 0 <= score <= 25, f"{tid} base score {score} out of range"

        # 4. Apply ranking + multiplier
        team_scores = [
            {"team_id": tid, "base_score": base_results[tid]} for tid in TEAM_IDS
        ]
        ranked = rank_teams(team_scores)
        graded = assign_grades(ranked)

        assert len(graded) == 5
        for entry in graded:
            assert entry["grade"] in ("A", "B", "C")
            assert entry["multiplier"] in (1, 2, 3)
            earned = entry["base_score"] * entry["multiplier"]
            assert entry["earned_points"] == earned

        # 5. Normalize AI accuracy /60
        phase1_scores = {}
        for entry in graded:
            team_data = {
                "team_id": entry["team_id"],
                "matches": [
                    {"match_id": "match-001", "earned_points": entry["earned_points"]}
                ],
            }
            norm = calculate_phase1_score(team_data)
            phase1_scores[norm["team_id"]] = norm["phase1_score"]

        assert len(phase1_scores) == 5
        for tid, score in phase1_scores.items():
            assert 0 <= score <= 60, f"{tid} phase1 score {score} out of range"

        # 6. Calculate technical score /20
        tech_evals = _load_technical()
        tech_scores = {}
        for ev in tech_evals:
            validated_tech = TechnicalEvaluation(**ev)
            result = calculate_technical_score(validated_tech.model_dump())
            tech_scores[result["team_id"]] = result["technical_score"]

        assert len(tech_scores) == 5
        for tid, score in tech_scores.items():
            assert 0 <= score <= 20, f"{tid} technical score {score} out of range"

        # 7. Calculate presentation score /20
        pres_evals = _load_presentation()
        for ev in pres_evals:
            PresentationEvaluation(**ev)
        pres_results = calculate_presentation_scores(pres_evals)

        pres_scores = {
            r["team_id"]: round((r["weighted_score"] / 150) * 20, 2)
            for r in pres_results
        }
        assert len(pres_scores) == 5
        for tid, score in pres_scores.items():
            assert 0 <= score <= 20, f"{tid} presentation score {score} out of range"

        # 8. Generate final leaderboard /100
        leaderboard_data = []
        for tid in TEAM_IDS:
            leaderboard_data.append({
                "team_id": tid,
                "phase1_score": phase1_scores[tid],
                "technical_score": tech_scores[tid],
                "presentation_score": pres_scores[tid],
            })

        leaderboard = calculate_leaderboard(leaderboard_data)

        # Verify
        all_teams_included = {entry["team_id"] for entry in leaderboard}
        assert all_teams_included == set(TEAM_IDS), (
            f"Missing teams: {set(TEAM_IDS) - all_teams_included}"
        )

        for entry in leaderboard:
            assert entry["final_score"] <= 100, (
                f"{entry['team_id']} final score {entry['final_score']} exceeds 100"
            )
            assert entry["rank"] >= 1
            assert entry["team_id"] in TEAM_IDS
            assert set(entry["scores"].keys()) == {
                "ai_accuracy",
                "technical",
                "presentation",
            }

        # Winner (rank 1) is generated
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[0]["final_score"] == max(
            e["final_score"] for e in leaderboard
        )

        # Leaderboard is sorted by rank ascending
        for i in range(len(leaderboard) - 1):
            assert leaderboard[i]["rank"] <= leaderboard[i + 1]["rank"]


    def test_schema_validation_enforced(self):
        import pytest
        from pydantic import ValidationError

        predictions = _load_predictions()
        for pred in predictions:
            PredictionSubmission(**pred)

        raw_actual = json.loads((FIXTURES / "actual_result.json").read_text())
        ActualResultSubmission(**raw_actual)

        tech_evals = _load_technical()
        for ev in tech_evals:
            TechnicalEvaluation(**ev)

        pres_evals = _load_presentation()
        for ev in pres_evals:
            PresentationEvaluation(**ev)

        invalid_pred = dict(predictions[0])
        invalid_pred["match_prediction"]["predicted_winner"] = "invalid"
        with pytest.raises(ValidationError):
            PredictionSubmission(**invalid_pred)

        invalid_result = dict(raw_actual)
        invalid_result["actual_winner"] = "invalid"
        with pytest.raises(ValidationError):
            ActualResultSubmission(**invalid_result)

    def test_all_scores_non_negative(self):
        predictions = _load_predictions()
        for pred in predictions:
            result = calculate_base_score(pred, ACTUAL, ACTUAL_PROBS)
            for k, v in result["breakdown"].items():
                assert v >= 0, f"{result['team_id']} {k} negative: {v}"
            assert result["base_score"] >= 0

        tech_evals = _load_technical()
        for ev in tech_evals:
            result = calculate_technical_score(ev)
            assert result["technical_score"] >= 0

        pres_results = calculate_presentation_scores(_load_presentation())
        for r in pres_results:
            assert r["weighted_score"] is None or r["weighted_score"] >= 0
