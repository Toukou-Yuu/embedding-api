from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import models, system
from app.backends.fake_backend import FakeBackend
from app.config import Settings
from app.errors import APIError, api_error_handler
from app.services.embedding_service import EmbeddingService
from app.services.model_registry import ModelRegistry
from app.utils.device import resolve_device
from app.utils.logging import configure_logging
from app.utils.timing import elapsed_ms, now


def build_backend(settings: Settings, registry: ModelRegistry):
    if settings.backend == "fake":
        return FakeBackend(registry.default())
    from app.backends.sentence_transformer_backend import SentenceTransformerBackend

    return SentenceTransformerBackend(settings, registry.default())


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or Settings()
    logger = configure_logging(runtime_settings.log_level)
    registry = ModelRegistry(runtime_settings)
    backend = build_backend(runtime_settings, registry)
    service = EmbeddingService(backend, registry)
    resolved_device = (
        "fake"
        if runtime_settings.backend == "fake"
        else resolve_device(runtime_settings.device)
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if runtime_settings.preload:
            try:
                service.load()
            except APIError as error:
                logger.error("model_preload_failed", extra={"error_code": error.code})
        yield

    app = FastAPI(title="embedding-api", version="1.0.0", lifespan=lifespan)
    app.state.settings = runtime_settings
    app.state.model_registry = registry
    app.state.embedding_service = service
    app.state.resolved_device = resolved_device
    app.state.logger = logger
    app.add_exception_handler(APIError, api_error_handler)
    app.include_router(system.router, prefix="/v1")
    app.include_router(models.router, prefix="/v1")

    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        started = now()
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": 500,
                    "latency_ms": elapsed_ms(started),
                    "error_code": "INTERNAL_ERROR",
                },
            )
            raise
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "latency_ms": elapsed_ms(started),
            },
        )
        return response

    @app.exception_handler(Exception)
    async def unhandled_error(_: Request, error: Exception) -> JSONResponse:
        logging.getLogger("embedding_api").exception("unhandled_error", exc_info=error)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "details": {},
                }
            },
        )

    return app


app = create_app()
