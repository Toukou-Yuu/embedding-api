from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request

from app.schemas import EmbeddingRequest, EmbeddingResponse

router = APIRouter(tags=["embeddings"])


@router.post("/embeddings", response_model=EmbeddingResponse, response_model_exclude_none=True)
async def create_embeddings(payload: EmbeddingRequest, request: Request) -> EmbeddingResponse:
    return await asyncio.to_thread(request.app.state.embedding_service.embed, payload)
