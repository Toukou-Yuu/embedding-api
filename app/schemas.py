from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class InputType(StrEnum):
    QUERY = "query"
    DOCUMENT = "document"


class EmbeddingRequest(BaseModel):
    model: str | None = None
    input: str | list[str]
    input_type: InputType = InputType.DOCUMENT
    normalize: bool = True
    truncate: bool = True
    return_usage: bool = True


class EmbeddingData(BaseModel):
    object: Literal["embedding"] = "embedding"
    index: int
    embedding: list[float]


class EmbeddingUsage(BaseModel):
    prompt_tokens: int | None = None
    total_tokens: int | None = None
    input_count: int


class EmbeddingResponse(BaseModel):
    object: Literal["list"] = "list"
    model: str
    dimension: int
    normalized: bool
    input_type: InputType
    data: list[EmbeddingData]
    usage: EmbeddingUsage | None = None
    vectors: list[list[float]] | None = None


class ModelInfo(BaseModel):
    name: str
    dimension: int
    normalized: bool
    recommended_distance: Literal["Cosine", "Dot", "Euclid"] = "Cosine"
    max_input_tokens: int | None = None
    supports_query_document_prefix: bool = True
    contract_version: str = "embedding-api.v1"


class ModelsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[ModelInfo]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["embedding-api"] = "embedding-api"
    version: str = "1.0.0"


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    service: Literal["embedding-api"] = "embedding-api"
    model_loaded: bool
    default_model: str | None = None
    device: str | None = None
    reason: str | None = None


class DeviceInfo(BaseModel):
    configured: str
    resolved: str | None


class RuntimeInfo(BaseModel):
    backend: str
    preload: bool
    max_batch_size: int
    max_input_chars: int


class ServiceInfoResponse(BaseModel):
    service: Literal["embedding-api"] = "embedding-api"
    version: str = "1.0.0"
    contract_version: Literal["embedding-api.v1"] = "embedding-api.v1"
    default_model: str
    device: DeviceInfo
    runtime: RuntimeInfo
    models: list[ModelInfo]


class ErrorContent(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorContent

