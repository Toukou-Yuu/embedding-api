from __future__ import annotations

from threading import BoundedSemaphore, Lock

from app.backends.base import EmbeddingBackend
from app.config import Settings
from app.errors import APIError
from app.schemas import EmbeddingRequest, EmbeddingResponse, EmbeddingUsage, ModelInfo
from app.services.model_registry import ModelRegistry
from app.services.text_preprocessor import preprocess_texts


class EmbeddingService:
    """Owns a single backend instance and serializes first-time model loading."""

    def __init__(
        self,
        backend: EmbeddingBackend,
        registry: ModelRegistry,
        settings: Settings,
    ) -> None:
        self._backend = backend
        self._registry = registry
        self._settings = settings
        self._load_lock = Lock()
        self._encode_semaphore = BoundedSemaphore(settings.encode_concurrency)
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

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        model_info = self._registry.resolve(request.model)
        texts = self._validate_input(request.input)
        self.load()
        prepared_texts = preprocess_texts(model_info.name, texts, request.input_type)
        vectors: list[list[float]] = []
        with self._encode_semaphore:
            for start in range(0, len(prepared_texts), self._settings.batch_size):
                batch = prepared_texts[start : start + self._settings.batch_size]
                vectors.extend(
                    self._backend.encode(
                        batch,
                        request.input_type,
                        request.normalize,
                        request.truncate,
                    )
                )
        if len(vectors) != len(texts):
            raise APIError("EMBEDDING_FAILED", "Backend returned an unexpected vector count", 500)
        usage = None
        if request.return_usage:
            token_count = self._backend.count_tokens(prepared_texts)
            usage = EmbeddingUsage(
                prompt_tokens=token_count,
                total_tokens=token_count,
                input_count=len(texts),
            )
        return EmbeddingResponse(
            model=model_info.name,
            dimension=len(vectors[0]),
            normalized=request.normalize,
            input_type=request.input_type,
            data=[{"index": index, "embedding": vector} for index, vector in enumerate(vectors)],
            usage=usage,
            vectors=vectors,
        )

    def _validate_input(self, value: str | list[str]) -> list[str]:
        texts = [value] if isinstance(value, str) else value
        if not texts:
            raise APIError("INVALID_REQUEST", "input must not be empty", 400)
        if len(texts) > self._settings.max_batch_size:
            raise APIError(
                "BATCH_TOO_LARGE",
                f"input count exceeds the limit of {self._settings.max_batch_size}",
                400,
            )
        for index, text in enumerate(texts):
            if not text.strip():
                raise APIError("INVALID_REQUEST", f"input at index {index} must not be blank", 400)
            if len(text) > self._settings.max_input_chars:
                raise APIError(
                    "INPUT_TOO_LONG",
                    f"input at index {index} exceeds the character limit",
                    400,
                )
        return texts
