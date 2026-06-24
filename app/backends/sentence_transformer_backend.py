from __future__ import annotations

from typing import Any

from app.config import Settings
from app.errors import APIError
from app.schemas import InputType, ModelInfo


class SentenceTransformerBackend:
    """SentenceTransformers implementation used for production inference."""

    def __init__(self, settings: Settings, configured_info: ModelInfo) -> None:
        self._settings = settings
        self._configured_info = configured_info
        self._model: Any | None = None
        self._tokenizer: Any | None = None
        self._max_input_tokens = settings.max_length

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self._settings.model,
                cache_folder=str(self._settings.model_cache_dir),
                device=self._settings.device,
            )
        except Exception as error:
            raise APIError("MODEL_LOAD_FAILED", "Model failed to load", 503) from error
        self._tokenizer = self._model.tokenizer
        model_limit = getattr(self._model, "max_seq_length", None)
        if isinstance(model_limit, int) and model_limit > 0:
            self._max_input_tokens = min(self._settings.max_length, model_limit)
        self._model.max_seq_length = self._max_input_tokens

    def is_loaded(self) -> bool:
        return self._model is not None

    def model_info(self) -> ModelInfo:
        if self._model is None:
            return self._configured_info
        dimension = self._model.get_sentence_embedding_dimension()
        if dimension is None:
            raise APIError("MODEL_LOAD_FAILED", "Model did not report an embedding dimension", 503)
        return self._configured_info.model_copy(
            update={"dimension": int(dimension), "max_input_tokens": self._max_input_tokens}
        )

    def encode(
        self,
        texts: list[str],
        input_type: InputType,
        normalize: bool,
        truncate: bool,
    ) -> list[list[float]]:
        del input_type
        if self._model is None or self._tokenizer is None:
            raise APIError("MODEL_NOT_READY", "Model is not loaded", 503)
        lengths = self._token_lengths(texts)
        if not truncate and any(length > self._max_input_tokens for length in lengths):
            raise APIError("INPUT_TOO_LONG", "Input exceeds the model token limit", 400)
        try:
            embeddings = self._model.encode(
                texts,
                batch_size=self._settings.batch_size,
                normalize_embeddings=normalize,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as error:
            raise APIError("EMBEDDING_FAILED", "Embedding generation failed", 500) from error
        return embeddings.tolist()

    def count_tokens(self, texts: list[str]) -> int | None:
        if self._tokenizer is None:
            return None
        return sum(self._token_lengths(texts))

    def _token_lengths(self, texts: list[str]) -> list[int]:
        if self._tokenizer is None:
            return []
        encoded = self._tokenizer(texts, add_special_tokens=True, truncation=False)
        return [len(token_ids) for token_ids in encoded["input_ids"]]

