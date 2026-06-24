from __future__ import annotations

import math

from fastapi.testclient import TestClient


def test_single_string_input(client: TestClient) -> None:
    response = client.post("/v1/embeddings", json={"input": "第一段文本"})

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "BAAI/bge-m3"
    assert body["dimension"] == 8
    assert body["input_type"] == "document"
    assert len(body["data"]) == 1
    assert body["data"][0]["index"] == 0
    assert len(body["data"][0]["embedding"]) == 8
    assert body["usage"]["input_count"] == 1


def test_list_input_and_order_are_stable(client: TestClient) -> None:
    response = client.post("/v1/embeddings", json={"input": ["first", "second", "third"]})
    single = client.post("/v1/embeddings", json={"input": "second"})

    assert response.status_code == 200
    assert [item["index"] for item in response.json()["data"]] == [0, 1, 2]
    assert response.json()["data"][1]["embedding"] == single.json()["data"][0]["embedding"]


def test_query_input_type_is_returned(client: TestClient) -> None:
    response = client.post("/v1/embeddings", json={"input": "question", "input_type": "query"})

    assert response.status_code == 200
    assert response.json()["input_type"] == "query"


def test_normalize_true_and_false(client: TestClient) -> None:
    normalized = client.post("/v1/embeddings", json={"input": "same", "normalize": True})
    raw = client.post("/v1/embeddings", json={"input": "same", "normalize": False})

    normalized_length = math.sqrt(sum(value**2 for value in normalized.json()["vectors"][0]))
    raw_length = math.sqrt(sum(value**2 for value in raw.json()["vectors"][0]))
    assert math.isclose(normalized_length, 1.0, rel_tol=1e-9)
    assert not math.isclose(raw_length, 1.0, rel_tol=1e-9)
    assert normalized.json()["normalized"] is True
    assert raw.json()["normalized"] is False


def test_vectors_compatibility_field_and_optional_usage(client: TestClient) -> None:
    response = client.post(
        "/v1/embeddings",
        json={"input": ["one", "two"], "return_usage": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["vectors"] == [item["embedding"] for item in body["data"]]
    assert "usage" not in body

