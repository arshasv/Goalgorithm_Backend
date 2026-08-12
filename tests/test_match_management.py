from datetime import datetime, timezone

def test_creating_duplicate_match_number_fails(client, organizer_headers, sample_match):
    # Try to create a match with match_number=1, which is already created by sample_match
    resp = client.post(
        "/api/v1/matches",
        json={
            "match_number": 1,
            "home_team_name": "Germany",
            "away_team_name": "France",
            "scheduled_at": datetime(2026, 6, 20, 20, 0, 0, tzinfo=timezone.utc).isoformat(),
        },
        headers=organizer_headers,
    )
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_adding_result_changes_status_to_completed(client, organizer_headers, sample_match):
    # Initially match should be SCHEDULED
    assert sample_match.status.value == "SCHEDULED"

    resp = client.post(
        "/api/v1/actual-results",
        json={
            "match_id": str(sample_match.id),
            "actual_winner": "home",
            "final_score": {
                "home_team_goals": 2,
                "away_team_goals": 1
            },
            "goal_scorers": {"home": ["Player A", "Player B"], "away": ["Player C"]},
            "player_results": [
                {"player_id": "p1", "player_name": "Player A", "actual_goals": 1},
                {"player_id": "p2", "player_name": "Player B", "actual_goals": 1},
                {"player_id": "p3", "player_name": "Player C", "actual_goals": 1}
            ]
        },
        headers=organizer_headers,
    )
    assert resp.status_code == 200, resp.json()

    # Fetch the match again to verify status updated to COMPLETED
    resp2 = client.get("/api/v1/matches", headers=organizer_headers)
    assert resp2.status_code == 200, resp2.json()
    
    matches = resp2.json()
    match = next(m for m in matches if m["id"] == str(sample_match.id))
    
    # Status MUST be COMPLETED
    assert match["status"] == "COMPLETED"


def test_match_api_returns_saved_scores(client, organizer_headers, sample_match):
    # Post a result
    resp_post = client.post(
        "/api/v1/actual-results",
        json={
            "match_id": str(sample_match.id),
            "actual_winner": "home",
            "final_score": {
                "home_team_goals": 3,
                "away_team_goals": 0
            },
            "goal_scorers": {"home": ["A", "B", "C"], "away": []},
            "player_results": [
                {"player_id": "pa", "player_name": "A", "actual_goals": 1},
                {"player_id": "pb", "player_name": "B", "actual_goals": 1},
                {"player_id": "pc", "player_name": "C", "actual_goals": 1}
            ]
        },
        headers=organizer_headers,
    )
    assert resp_post.status_code == 200, resp_post.json()

    # Call get matches API
    resp = client.get("/api/v1/matches", headers=organizer_headers)
    assert resp.status_code == 200, resp.json()
    matches = resp.json()
    
    # Verify scores are returned
    match = next(m for m in matches if m["id"] == str(sample_match.id))
    
    assert match["actual_home_goals"] == 3
    assert match["actual_away_goals"] == 0
