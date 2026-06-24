from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def app_factory():
    def build(**overrides: object):
        defaults: dict[str, object] = {
            "backend": "fake",
            "preload": True,
            "fake_dimension": 8,
            "model": "BAAI/bge-m3",
        }
        defaults.update(overrides)
        return create_app(Settings(**defaults))

    return build


@pytest.fixture
def client(app_factory) -> TestClient:
    with TestClient(app_factory()) as test_client:
        yield test_client
