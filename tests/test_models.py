from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_models(client: TestClient) -> None:
    response = client.get("/v1/models")

    assert response.status_code == 200
    assert response.json()["object"] == "list"
    assert response.json()["data"][0]["name"] == "BAAI/bge-m3"


def test_get_model_with_slash_in_name(client: TestClient) -> None:
    response = client.get("/v1/models/BAAI/bge-m3")

    assert response.status_code == 200
    assert response.json()["dimension"] == 8


def test_model_not_found(client: TestClient) -> None:
    response = client.get("/v1/models/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODEL_NOT_FOUND"

