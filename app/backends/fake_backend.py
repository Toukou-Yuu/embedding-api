from __future__ import annotations

import hashlib
import math

from app.errors import APIError
from app.schemas import InputType, ModelInfo


class FakeBackend:
    """Deterministic, dependency-free backend for tests and smoke checks."""

    def __init__(self, model_info: ModelInfo) -> None:
        self._model_info = model_info
        self._loaded = False

    def load(self) -> None:
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def model_info(self) -> ModelInfo:
        return self._model_info

    def encode(
        self,
        texts: list[str],
        input_type: InputType,
        normalize: bool,
        truncate: bool,
    ) -> list[list[float]]:
        del input_type
        if not self._loaded:
            raise RuntimeError("Fake backend has not been loaded")
        max_tokens = self._model_info.max_input_tokens
        if max_tokens is not None and not truncate:
            if any(len(text.split()) > max_tokens for text in texts):
                raise APIError("INPUT_TOO_LONG", "Input exceeds the model token limit", 400)
        return [
            self._vector_for_text(self._truncate(text, max_tokens), normalize) for text in texts
        ]

    def count_tokens(self, texts: list[str]) -> int:
        max_tokens = self._model_info.max_input_tokens
        if max_tokens is None:
            return sum(len(text.split()) for text in texts)
        return sum(min(len(text.split()), max_tokens) for text in texts)

    def _vector_for_text(self, text: str, normalize: bool) -> list[float]:
        values: list[float] = []
        counter = 0
        while len(values) < self._model_info.dimension:
            digest = hashlib.sha512(f"{counter}:{text}".encode()).digest()
            values.extend((byte / 127.5) - 1.0 for byte in digest)
            counter += 1
        vector = values[: self._model_info.dimension]
        if not normalize:
            return vector
        magnitude = math.sqrt(sum(value * value for value in vector))
        return [value / magnitude for value in vector]

    @staticmethod
    def _truncate(text: str, max_tokens: int | None) -> str:
        if max_tokens is None:
            return text
        return " ".join(text.split()[:max_tokens])
