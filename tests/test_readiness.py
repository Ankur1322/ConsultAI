from fastapi.testclient import TestClient

from consultai.main import app


def test_readiness_endpoint_is_available_without_database() -> None:
    response = TestClient(app).get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
