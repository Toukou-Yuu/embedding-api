from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_REAL_MODEL_TESTS") != "1",
    reason="set RUN_REAL_MODEL_TESTS=1 to download and test BGE-M3",
)


def test_bge_m3_generates_normalized_embeddings() -> None:
    settings = Settings(
        backend="sentence-transformers",
        model="BAAI/bge-m3",
        device="auto",
        preload=True,
        model_cache_dir=Path("data/models"),
    )
    with TestClient(create_app(settings)) as client:
        response = client.post("/v1/embeddings", json={"input": "本地 BGE-M3 推理测试"})

    assert response.status_code == 200
    body = response.json()
    assert body["dimension"] == 1024
    assert len(body["data"][0]["embedding"]) == 1024
    assert body["normalized"] is True

