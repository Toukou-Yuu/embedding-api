from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    settings = Settings(backend="fake", preload=True, fake_dimension=8, model="BAAI/bge-m3")
    with TestClient(create_app(settings)) as test_client:
        yield test_client

