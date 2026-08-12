"""Tests for Leaderboard Visibility Configuration feature."""

from app.models.leaderboard import LeaderboardModel
from app.models.leaderboard_visibility import LeaderboardVisibilityModel
from app.models.team import TeamModel


def _create_leaderboard_entry(db_session, team_id, rank, phase1, tech, pres):
    import uuid
    uid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
    entry = LeaderboardModel(
        team_id=uid,
        rank=rank,
        phase1_score=phase1,
        technical_score=tech,
        presentation_score=pres,
        final_score=phase1 + tech + pres,
    )
    db_session.add(entry)
    db_session.commit()
    return entry


class TestLeaderboardVisibilitySettingsAPI:
    """Tests for GET/PUT /admin/leaderboard/settings."""

    def test_organizer_can_get_settings(self, client, organizer_headers):
        resp = client.get("/api/v1/admin/leaderboard/settings", headers=organizer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["show_all_teams_leaderboard"] is True
        assert body["show_rank"] is True
        assert body["show_team_name"] is True
        assert body["show_phase_1_score"] is True
        assert body["show_technical_score"] is True
        assert body["show_presentation_score"] is True
        assert body["show_final_score"] is True
        assert "id" in body
        assert "updated_at" in body

    def test_organizer_can_update_settings(self, client, organizer_headers):
        resp = client.put(
            "/api/v1/admin/leaderboard/settings",
            json={"show_all_teams_leaderboard": False, "show_final_score": False},
            headers=organizer_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["show_all_teams_leaderboard"] is False
        assert body["show_final_score"] is False
        assert body["show_rank"] is True

    def test_team_leader_cannot_get_settings(self, client, team_leader_headers):
        resp = client.get("/api/v1/admin/leaderboard/settings", headers=team_leader_headers)
        assert resp.status_code == 403

    def test_team_leader_cannot_update_settings(self, client, team_leader_headers):
        resp = client.put(
            "/api/v1/admin/leaderboard/settings",
            json={"show_final_score": False},
            headers=team_leader_headers,
        )
        assert resp.status_code == 403

    def test_settings_persist_across_calls(self, client, organizer_headers):
        client.put(
            "/api/v1/admin/leaderboard/settings",
            json={"show_rank": False},
            headers=organizer_headers,
        )
        resp = client.get("/api/v1/admin/leaderboard/settings", headers=organizer_headers)
        assert resp.json()["show_rank"] is False


class TestLeaderboardVisibilityFiltering:
    """Tests for visibility filtering on GET /leaderboard."""

    def test_default_returns_all_fields(self, client, organizer_headers, team_a, db_session):
        _create_leaderboard_entry(db_session, str(team_a.id), 1, 50, 18, 16)
        resp = client.get("/api/v1/leaderboard", headers=organizer_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        entry = body[0]
        assert "rank" in entry
        assert "team_name" in entry
        assert "phase1_score" in entry
        assert "technical_score" in entry
        assert "presentation_score" in entry
        assert "final_score" in entry

    def test_disabled_fields_removed_for_team_leader(self, client, organizer_headers, team_leader_headers, team_a, db_session):
        _create_leaderboard_entry(db_session, str(team_a.id), 1, 50, 18, 16)
        client.put(
            "/api/v1/admin/leaderboard/settings",
            json={"show_phase_1_score": False, "show_technical_score": False, "show_final_score": False},
            headers=organizer_headers,
        )
        resp = client.get("/api/v1/leaderboard", headers=team_leader_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        entry = body[0]
        assert "rank" in entry
        assert "team_name" in entry
        assert "phase1_score" not in entry
        assert "technical_score" not in entry
        assert "presentation_score" in entry
        assert "final_score" not in entry

    def test_show_all_teams_false_only_returns_own_team(self, client, organizer_headers, team_leader_headers, team_a, db_session):
        team_b = TeamModel(team_id="B", name="Team B", code="B", team_leader_name="Leader B")
        db_session.add(team_b)
        db_session.commit()
        _create_leaderboard_entry(db_session, str(team_a.id), 1, 50, 18, 16)
        _create_leaderboard_entry(db_session, str(team_b.id), 2, 40, 15, 14)
        client.put(
            "/api/v1/admin/leaderboard/settings",
            json={"show_all_teams_leaderboard": False},
            headers=organizer_headers,
        )
        resp = client.get("/api/v1/leaderboard", headers=team_leader_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["team_id"] == str(team_a.id)

    def test_phase_scores_master_toggle(self, client, organizer_headers, team_leader_headers, team_a, db_session):
        _create_leaderboard_entry(db_session, str(team_a.id), 1, 50, 18, 16)
        client.put(
            "/api/v1/admin/leaderboard/settings",
            json={"show_phase_scores": False},
            headers=organizer_headers,
        )
        resp = client.get("/api/v1/leaderboard", headers=team_leader_headers)
        body = resp.json()
        assert len(body) == 1
        entry = body[0]
        assert "phase1_score" not in entry
        assert "technical_score" not in entry
        assert "presentation_score" not in entry
        assert "final_score" in entry

    def test_organizer_always_sees_all_fields(self, client, organizer_headers, team_a, db_session):
        _create_leaderboard_entry(db_session, str(team_a.id), 1, 50, 18, 16)
        client.put(
            "/api/v1/admin/leaderboard/settings",
            json={"show_final_score": False, "show_phase_1_score": False},
            headers=organizer_headers,
        )
        resp = client.get("/api/v1/leaderboard", headers=organizer_headers)
        body = resp.json()
        assert len(body) == 1
        entry = body[0]
        assert "final_score" in entry
        assert "phase1_score" in entry
