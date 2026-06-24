from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_does_not_depend_on_model(client: TestClient) -> None:
    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "embedding-api", "version": "1.0.0"}


def test_ready_with_preloaded_fake_backend(client: TestClient) -> None:
    response = client.get("/v1/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["model_loaded"] is True
    assert response.json()["device"] == "fake"


def test_info_exposes_runtime_contract(client: TestClient) -> None:
    response = client.get("/v1/info")

    assert response.status_code == 200
    body = response.json()
    assert body["contract_version"] == "embedding-api.v1"
    assert body["runtime"]["backend"] == "fake"
    assert body["models"][0]["dimension"] == 8

