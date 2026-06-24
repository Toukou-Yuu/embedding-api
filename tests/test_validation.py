from __future__ import annotations

from fastapi.testclient import TestClient


def test_empty_input_is_rejected(client: TestClient) -> None:
    for value in ("", [], ["   "]):
        response = client.post("/v1/embeddings", json={"input": value})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_batch_too_large_is_rejected(app_factory) -> None:
    with TestClient(app_factory(batch_size=1, max_batch_size=1)) as client:
        response = client.post("/v1/embeddings", json={"input": ["one", "two"]})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BATCH_TOO_LARGE"


def test_input_too_long_is_rejected(app_factory) -> None:
    with TestClient(app_factory(max_input_chars=4)) as client:
        response = client.post(
            "/v1/embeddings",
            json={"input": "five!", "truncate": False},
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INPUT_TOO_LONG"


def test_invalid_input_type_uses_standard_error_envelope(client: TestClient) -> None:
    response = client.post("/v1/embeddings", json={"input": "text", "input_type": "invalid"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_api_key_protects_v1_interfaces_except_health(app_factory) -> None:
    with TestClient(app_factory(require_api_key=True, api_key="secret")) as client:
        health = client.get("/v1/health")
        protected = client.get("/v1/info")
        authorized = client.get("/v1/info", headers={"Authorization": "Bearer secret"})

    assert health.status_code == 200
    assert protected.status_code == 401
    assert protected.json()["error"]["code"] == "UNAUTHORIZED"
    assert authorized.status_code == 200


def test_lazy_load_transitions_ready_state(app_factory) -> None:
    with TestClient(app_factory(preload=False)) as client:
        before = client.get("/v1/ready")
        embedding = client.post("/v1/embeddings", json={"input": "loads fake backend"})
        after = client.get("/v1/ready")

    assert before.status_code == 503
    assert before.json()["status"] == "not_ready"
    assert embedding.status_code == 200
    assert after.status_code == 200
    assert after.json()["status"] == "ready"
