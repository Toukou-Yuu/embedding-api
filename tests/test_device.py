from __future__ import annotations

import pytest

from app.errors import APIError
from app.utils.device import resolve_device


def test_auto_device_falls_back_to_cpu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.utils.device.torch.cuda.is_available", lambda: False)
    monkeypatch.setattr("app.utils.device.torch.backends.mps.is_available", lambda: False)

    assert resolve_device("auto") == "cpu"


def test_unavailable_explicit_device_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.utils.device.torch.cuda.is_available", lambda: False)
    monkeypatch.setattr("app.utils.device.torch.backends.mps.is_available", lambda: False)

    with pytest.raises(APIError, match="Configured CUDA device is unavailable"):
        resolve_device("cuda")

