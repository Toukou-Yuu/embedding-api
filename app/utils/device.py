from __future__ import annotations

import torch

from app.errors import APIError


def resolve_device(configured_device: str) -> str:
    """Resolve an explicit device or select the best available local device."""
    cuda_available = torch.cuda.is_available()
    mps_available = torch.backends.mps.is_available()

    if configured_device == "auto":
        if cuda_available:
            return "cuda"
        if mps_available:
            return "mps"
        return "cpu"
    if configured_device == "cuda" and not cuda_available:
        raise APIError("DEVICE_UNAVAILABLE", "Configured CUDA device is unavailable", 503)
    if configured_device == "mps" and not mps_available:
        raise APIError("DEVICE_UNAVAILABLE", "Configured MPS device is unavailable", 503)
    return configured_device

