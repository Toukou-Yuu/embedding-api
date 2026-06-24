from __future__ import annotations

from fastapi.testclient import TestClient


def test_embedding_response_matches_retrieval_api_contract(client: TestClient) -> None:
    response = client.post(
        "/v1/embeddings",
        json={"model": "BAAI/bge-m3", "input": ["alpha", "beta"], "input_type": "document"},
    )

    assert response.status_code == 200
    body = response.json()
    vectors = [item["embedding"] for item in body["data"]]
    assert body["object"] == "list"
    assert body["model"] == "BAAI/bge-m3"
    assert body["dimension"] == 8
    assert body["normalized"] is True
    assert body["input_type"] == "document"
    assert body["vectors"] == vectors
    assert len(vectors) == body["usage"]["input_count"] == 2

