from __future__ import annotations

from app.config import Settings
from app.errors import ModelNotFoundError
from app.schemas import ModelInfo

KNOWN_MODEL_DIMENSIONS = {"BAAI/bge-m3": 1024}


class ModelRegistry:
    """The v1 service exposes one configured model at a time."""

    def __init__(self, settings: Settings) -> None:
        dimension = (
            settings.fake_dimension
            if settings.backend == "fake"
            else KNOWN_MODEL_DIMENSIONS.get(settings.model, 1024)
        )
        self._model_info = ModelInfo(
            name=settings.model,
            dimension=dimension,
            normalized=settings.normalize,
            recommended_distance=settings.recommended_distance,
            max_input_tokens=settings.max_length,
        )

    def default(self) -> ModelInfo:
        return self._model_info

    def list(self) -> list[ModelInfo]:
        return [self._model_info]

    def get(self, model_name: str) -> ModelInfo:
        if model_name != self._model_info.name:
            raise ModelNotFoundError(model_name)
        return self._model_info

    def resolve(self, model_name: str | None) -> ModelInfo:
        return self._model_info if model_name is None else self.get(model_name)

    def update_runtime_info(self, model_info: ModelInfo) -> None:
        self._model_info = model_info

