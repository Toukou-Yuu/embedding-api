from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.schemas import HealthResponse, ReadyResponse, ServiceInfoResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=ReadyResponse)
async def ready(request: Request) -> ReadyResponse | JSONResponse:
    service = request.app.state.embedding_service
    settings = request.app.state.settings
    if service.is_loaded():
        return ReadyResponse(
            status="ready",
            model_loaded=True,
            default_model=settings.model,
            device=request.app.state.resolved_device,
        )
    error = service.load_error()
    reason = "model_not_loaded" if error is None else error.code.lower()
    response = ReadyResponse(status="not_ready", model_loaded=False, reason=reason)
    return JSONResponse(status_code=503, content=response.model_dump(exclude_none=True))


@router.get("/info", response_model=ServiceInfoResponse)
async def info(request: Request) -> ServiceInfoResponse:
    settings = request.app.state.settings
    registry = request.app.state.model_registry
    return ServiceInfoResponse(
        default_model=settings.model,
        device={"configured": settings.device, "resolved": request.app.state.resolved_device},
        runtime={
            "backend": settings.backend,
            "preload": settings.preload,
            "max_batch_size": settings.max_batch_size,
            "max_input_chars": settings.max_input_chars,
        },
        models=registry.list(),
    )

