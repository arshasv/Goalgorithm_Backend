import uuid
from io import BytesIO

def test_upload_non_pkl_rejected(client, db_session, organizer_headers, sample_match, team_a):
    response = client.post(
        "/api/v1/model-execution/upload",
        headers=organizer_headers,
        data={"match_id": str(sample_match.id), "team_id": str(team_a.id)},
        files={"file": ("model.txt", BytesIO(b"dummy data"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Only .pkl files are allowed" in response.json()["detail"]

def test_upload_pkl_success(client, db_session, organizer_headers, sample_match, team_a):
    response = client.post(
        "/api/v1/model-execution/upload",
        headers=organizer_headers,
        data={"match_id": str(sample_match.id), "team_id": str(team_a.id)},
        files={"file": ("model.pkl", BytesIO(b"dummy pkl data"), "application/octet-stream")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "model_id" in data
    assert data["status"] == "IDLE"

    # Now get status
    status_resp = client.get(
        f"/api/v1/model-execution/{data['model_id']}/status",
        headers=organizer_headers
    )
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "IDLE"
    assert status_data["error_message"] is None

import pickle
import time

class DummyModelSuccess:
    def predict(self, model_input=None):
        return {
            "predicted_winner": "home",
            "score": {"teamA": 2, "teamB": 1},
            "confidence": 95
        }

class DummyModelFailure:
    def predict(self, model_input=None):
        raise ValueError("Simulated crash")

def test_execute_model_success(client, db_session, organizer_headers, sample_match, team_a):
    model = DummyModelSuccess()
    model_bytes = pickle.dumps(model)

    response = client.post(
        "/api/v1/model-execution/upload",
        headers=organizer_headers,
        data={"match_id": str(sample_match.id), "team_id": str(team_a.id)},
        files={"file": ("model.pkl", BytesIO(model_bytes), "application/octet-stream")}
    )
    model_id = response.json()["model_id"]

    exec_response = client.post(
        f"/api/v1/model-execution/{model_id}/execute",
        headers=organizer_headers
    )
    assert exec_response.status_code == 200
    exec_data = exec_response.json()
    assert exec_data["status"] == "RUNNING"
    execution_id = exec_data["execution_id"]

    # Wait for background task to finish
    time.sleep(0.5)

    status_resp = client.get(
        f"/api/v1/model-execution/{execution_id}/status",
        headers=organizer_headers
    )
    status_data = status_resp.json()
    assert status_data["status"] == "SUCCESS", f"Execution failed: {status_data}"
    assert status_data["prediction_id"] is not None

def test_execute_model_failure(client, db_session, organizer_headers, sample_match, team_a):
    model = DummyModelFailure()
    model_bytes = pickle.dumps(model)

    response = client.post(
        "/api/v1/model-execution/upload",
        headers=organizer_headers,
        data={"match_id": str(sample_match.id), "team_id": str(team_a.id)},
        files={"file": ("model.pkl", BytesIO(model_bytes), "application/octet-stream")}
    )
    model_id = response.json()["model_id"]

    exec_response = client.post(
        f"/api/v1/model-execution/{model_id}/execute",
        headers=organizer_headers
    )
    execution_id = exec_response.json()["execution_id"]

    time.sleep(0.5)

    status_resp = client.get(
        f"/api/v1/model-execution/{execution_id}/status",
        headers=organizer_headers
    )
    status_data = status_resp.json()
    assert status_data["status"] == "FAILED"
    assert "Simulated crash" in status_data["error_message"]

