from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request

from app.schemas import EmbeddingRequest, EmbeddingResponse

router = APIRouter(tags=["embeddings"])


@router.post("/embeddings", response_model=EmbeddingResponse, response_model_exclude_none=True)
async def create_embeddings(payload: EmbeddingRequest, request: Request) -> EmbeddingResponse:
    response = await asyncio.to_thread(request.app.state.embedding_service.embed, payload)
    request.state.model = response.model
    request.state.input_count = len(response.data)
    return response
