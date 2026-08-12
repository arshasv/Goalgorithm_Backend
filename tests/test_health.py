from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_running(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "running"}

    def test_health_method_not_allowed(self):
        resp = client.post("/health")
        assert resp.status_code == 405


class TestVersion:
    def test_version_returns_app_and_version(self):
        resp = client.get("/version")
        assert resp.status_code == 200
        body = resp.json()
        assert "app" in body
        assert "version" in body
        assert body["version"] == "0.1.0"

    def test_version_method_not_allowed(self):
        resp = client.post("/version")
        assert resp.status_code == 405
