from __future__ import annotations

from threading import Lock

from app.backends.base import EmbeddingBackend
from app.errors import APIError
from app.schemas import ModelInfo
from app.services.model_registry import ModelRegistry


class EmbeddingService:
    """Owns a single backend instance and serializes first-time model loading."""

    def __init__(self, backend: EmbeddingBackend, registry: ModelRegistry) -> None:
        self._backend = backend
        self._registry = registry
        self._load_lock = Lock()
        self._load_error: APIError | None = None

    def load(self) -> None:
        if self._backend.is_loaded():
            return
        with self._load_lock:
            if self._backend.is_loaded():
                return
            try:
                self._backend.load()
                self._registry.update_runtime_info(self._backend.model_info())
                self._load_error = None
            except APIError as error:
                self._load_error = error
                raise
            except Exception as error:
                self._load_error = APIError("MODEL_LOAD_FAILED", "Model failed to load", 503)
                raise self._load_error from error

    def is_loaded(self) -> bool:
        return self._backend.is_loaded()

    def load_error(self) -> APIError | None:
        return self._load_error

    def model_info(self) -> ModelInfo:
        return self._registry.default()

