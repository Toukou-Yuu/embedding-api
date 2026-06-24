from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from hmac import compare_digest

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import embeddings, models, system
from app.backends.fake_backend import FakeBackend
from app.config import Settings
from app.errors import APIError, api_error_handler
from app.services.embedding_service import EmbeddingService
from app.services.model_registry import ModelRegistry
from app.utils.device import resolve_device
from app.utils.logging import configure_logging
from app.utils.timing import elapsed_ms, now


def build_backend(settings: Settings, registry: ModelRegistry, resolved_device: str):
    if settings.backend == "fake":
        return FakeBackend(registry.default())
    from app.backends.sentence_transformer_backend import SentenceTransformerBackend

    return SentenceTransformerBackend(settings, registry.default(), resolved_device)


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or Settings()
    logger = configure_logging(runtime_settings.log_level)
    registry = ModelRegistry(runtime_settings)
    resolved_device = (
        "fake"
        if runtime_settings.backend == "fake"
        else resolve_device(runtime_settings.device)
    )
    backend = build_backend(runtime_settings, registry, resolved_device)
    service = EmbeddingService(backend, registry, runtime_settings)

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
    app.add_exception_handler(RequestValidationError, request_validation_error)
    app.include_router(system.router, prefix="/v1")
    app.include_router(models.router, prefix="/v1")
    app.include_router(embeddings.router, prefix="/v1")

    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        started = now()
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        try:
            if _requires_authentication(request, runtime_settings):
                authorization = request.headers.get("Authorization", "")
                if not compare_digest(authorization, f"Bearer {runtime_settings.api_key}"):
                    request.state.error_code = "UNAUTHORIZED"
                    response = JSONResponse(
                        status_code=401,
                        content={
                            "error": {
                                "code": "UNAUTHORIZED",
                                "message": "Invalid or missing API key",
                                "details": {},
                            }
                        },
                    )
                else:
                    response = await call_next(request)
            else:
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
                "model": getattr(request.state, "model", None),
                "input_count": getattr(request.state, "input_count", None),
                "device": resolved_device,
                "error_code": getattr(request.state, "error_code", None),
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


def _requires_authentication(request: Request, settings: Settings) -> bool:
    if not settings.require_api_key or not request.url.path.startswith("/v1/"):
        return False
    if request.url.path == "/v1/health":
        return False
    if request.url.path == "/v1/ready" and not settings.require_api_key_for_ready:
        return False
    return True


async def request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    request.state.error_code = "INVALID_REQUEST"
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request validation failed",
                "details": {"validation_errors": exc.errors()},
            }
        },
    )


app = create_app()
