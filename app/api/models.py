from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas import ModelInfo, ModelsResponse

router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelsResponse)
async def list_models(request: Request) -> ModelsResponse:
    return ModelsResponse(data=request.app.state.model_registry.list())


@router.get("/models/{model_name:path}", response_model=ModelInfo)
async def get_model(model_name: str, request: Request) -> ModelInfo:
    return request.app.state.model_registry.get(model_name)

