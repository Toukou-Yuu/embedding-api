from __future__ import annotations

from typing import Protocol

from app.schemas import InputType, ModelInfo


class EmbeddingBackend(Protocol):
    def load(self) -> None: ...

    def is_loaded(self) -> bool: ...

    def model_info(self) -> ModelInfo: ...

    def encode(
        self,
        texts: list[str],
        input_type: InputType,
        normalize: bool,
        truncate: bool,
    ) -> list[list[float]]: ...

    def count_tokens(self, texts: list[str]) -> int | None: ...

