from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="EMBEDDING_", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8100
    backend: Literal["sentence-transformers", "fake"] = "sentence-transformers"
    model: str = "BAAI/bge-m3"
    device: Literal["auto", "cpu", "cuda", "mps"] = "auto"
    preload: bool = True
    batch_size: int = 16
    max_batch_size: int = 32
    max_input_chars: int = 12000
    max_length: int = 8192
    normalize: bool = True
    recommended_distance: Literal["Cosine", "Dot", "Euclid"] = "Cosine"
    model_cache_dir: Path = Path("./data/models")
    encode_concurrency: int = 1
    fake_dimension: int = 16
    api_key: str = ""
    require_api_key: bool = False
    require_api_key_for_ready: bool = False
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @model_validator(mode="after")
    def validate_limits(self) -> Settings:
        if not self.model.strip():
            raise ValueError("EMBEDDING_MODEL must not be blank")
        if self.batch_size < 1:
            raise ValueError("EMBEDDING_BATCH_SIZE must be at least 1")
        if self.max_batch_size < 1:
            raise ValueError("EMBEDDING_MAX_BATCH_SIZE must be at least 1")
        if self.batch_size > self.max_batch_size:
            raise ValueError("EMBEDDING_BATCH_SIZE cannot exceed EMBEDDING_MAX_BATCH_SIZE")
        if self.max_input_chars < 1 or self.max_length < 1:
            raise ValueError("input limits must be at least 1")
        if self.encode_concurrency < 1 or self.fake_dimension < 1:
            raise ValueError("concurrency and fake dimension must be at least 1")
        if self.require_api_key and not self.api_key:
            raise ValueError("EMBEDDING_API_KEY is required when authentication is enabled")
        return self

