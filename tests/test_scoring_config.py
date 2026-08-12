from datetime import datetime, timezone
from pathlib import Path

from app.models.enums import MatchStatus
from app.models.match import MatchModel
from app.models.score import ScoreModel

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    import json
    return json.loads((FIXTURES / name).read_text())


def _patch_payload(payload: dict, team_id: str | None = None, match_id: str | None = None) -> dict:
    result = payload.copy()
    if team_id:
        result["team_id"] = team_id
    if match_id:
        result["match_id"] = match_id
    return result


def _create_match(db_session, match_number=2):
    match = MatchModel(
        match_number=match_number,
        home_team_name="Argentina",
        away_team_name="Uruguay",
        scheduled_at=datetime(2026, 6, 20, 20, 0, 0, tzinfo=timezone.utc),
        freeze_deadline=datetime(2026, 6, 19, 20, 0, 0, tzinfo=timezone.utc),
        status=MatchStatus.SCHEDULED,
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)
    return match


DEFAULT_CONFIG_ID = "00000000-0000-0000-0000-000000000001"


class TestScoringConfigAPI:
    """Integration tests for Scoring Configuration."""

    def test_get_guidelines(self, client, default_scoring_config):
        resp = client.get("/api/v1/admin/scoring-config/guidelines")
        assert resp.status_code == 200
        body = resp.json()
        assert body["config"]["name"] == "Test Default"
        assert len(body["guidelines"]) == 25
        assert body["guidelines"][0]["key"] == "winner_points_correct"

    def test_organizer_creates_config(self, client, organizer_headers):
        resp = client.post(
            "/api/v1/admin/scoring-config",
            json={"name": "Custom Config", "winner_points_correct": 10},
            headers=organizer_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Custom Config"
        assert body["winner_points_correct"] == 10
        assert body["is_active"] is True
        assert body["version"] == 1

    def test_organizer_updates_config(self, client, organizer_headers, default_scoring_config):
        resp = client.put(
            f"/api/v1/admin/scoring-config/{DEFAULT_CONFIG_ID}",
            json={"winner_points_correct": 8, "probability_threshold": 20.0},
            headers=organizer_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["winner_points_correct"] == 8
        assert body["probability_threshold"] == 20.0
        assert body["scoreline_points_exact"] == 10

    def test_team_cannot_update_config(self, client, team_leader_headers, default_scoring_config):
        resp = client.put(
            f"/api/v1/admin/scoring-config/{DEFAULT_CONFIG_ID}",
            json={"winner_points_correct": 10},
            headers=team_leader_headers,
        )
        assert resp.status_code == 403

    def test_team_cannot_create_config(self, client, team_leader_headers):
        resp = client.post(
            "/api/v1/admin/scoring-config",
            json={"name": "Hacked Config"},
            headers=team_leader_headers,
        )
        assert resp.status_code == 403

    def test_organizer_can_reset_config(self, client, organizer_headers, db_session):
        client.post(
            "/api/v1/admin/scoring-config",
            json={"name": "Custom", "winner_points_correct": 99},
            headers=organizer_headers,
        )
        reset_resp = client.post("/api/v1/admin/scoring-config/reset", headers=organizer_headers)
        assert reset_resp.status_code == 200
        body = reset_resp.json()
        assert body["id"] == DEFAULT_CONFIG_ID
        assert body["winner_points_correct"] == 5

    def test_new_config_affects_new_scores(self, client, organizer_headers, team_a, sample_match, db_session, default_scoring_config):
        pred = _patch_payload(
            _load("valid_prediction.json"),
            team_id=str(team_a.id),
            match_id=str(sample_match.id),
        )
        actual = _patch_payload(_load("actual_result.json"), match_id=str(sample_match.id))
        resp = client.post(
            "/api/v1/calculate-match-score",
            json={"prediction": pred, "actual_result": actual},
            headers=organizer_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["breakdown"]["winner_score"] == 5

        cfg_resp = client.post(
            "/api/v1/admin/scoring-config",
            json={"name": "High Winner", "winner_points_correct": 10},
            headers=organizer_headers,
        )
        assert cfg_resp.json()["is_active"] is True

        match2 = _create_match(db_session, match_number=2)
        pred2 = _patch_payload(
            _load("valid_prediction.json"),
            team_id=str(team_a.id),
            match_id=str(match2.id),
        )
        actual2 = _patch_payload(_load("actual_result.json"), match_id=str(match2.id))
        resp2 = client.post(
            "/api/v1/calculate-match-score",
            json={"prediction": pred2, "actual_result": actual2},
            headers=organizer_headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["breakdown"]["winner_score"] == 10

    def test_old_scores_preserved_after_config_change(self, client, organizer_headers, team_a, sample_match, db_session, default_scoring_config):
        pred = _patch_payload(
            _load("valid_prediction.json"),
            team_id=str(team_a.id),
            match_id=str(sample_match.id),
        )
        actual = _patch_payload(_load("actual_result.json"), match_id=str(sample_match.id))
        calc_resp = client.post(
            "/api/v1/calculate-match-score",
            json={"prediction": pred, "actual_result": actual},
            headers=organizer_headers,
        )
        assert calc_resp.status_code == 200
        old_breakdown = calc_resp.json()["breakdown"]

        old_score_db = db_session.query(ScoreModel).filter(
            ScoreModel.team_id == team_a.id,
            ScoreModel.match_id == sample_match.id,
        ).first()
        assert old_score_db is not None
        assert old_score_db.config_id == DEFAULT_CONFIG_ID
        assert old_score_db.winner_points == old_breakdown["winner_score"]
        assert old_score_db.scoreline_points == old_breakdown["scoreline_score"]
        assert old_score_db.probability_points == old_breakdown["probability_score"]
        assert old_score_db.player_points == old_breakdown["player_score"]

        client.post(
            "/api/v1/admin/scoring-config",
            json={"name": "Changed Config", "winner_points_correct": 99},
            headers=organizer_headers,
        )

        old_score_again = db_session.query(ScoreModel).filter(
            ScoreModel.team_id == team_a.id,
            ScoreModel.match_id == sample_match.id,
        ).first()
        assert old_score_again is not None
        assert old_score_again.config_id == DEFAULT_CONFIG_ID
        assert old_score_again.winner_points == old_breakdown["winner_score"]
