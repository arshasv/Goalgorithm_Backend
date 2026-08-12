import pytest
from fastapi.testclient import TestClient

def test_team_breakdown_requires_auth(client: TestClient):
    response = client.get("/api/v1/reports/team-breakdown")
    assert response.status_code == 401

def test_team_breakdown_success(client: TestClient, organizer_headers: dict):
    response = client.get("/api/v1/reports/team-breakdown", headers=organizer_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_multiplier_impact_success(client: TestClient, organizer_headers: dict):
    response = client.get("/api/v1/reports/multiplier-impact", headers=organizer_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_rank_analysis_success(client: TestClient, organizer_headers: dict):
    response = client.get("/api/v1/reports/rank-analysis", headers=organizer_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_phase_contribution_success(client: TestClient, organizer_headers: dict):
    response = client.get("/api/v1/reports/phase-contribution", headers=organizer_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
