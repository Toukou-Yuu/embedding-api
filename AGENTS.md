# AGENTS.md

## Project Goal

`embedding-api` is a standalone text embedding HTTP service for local agent infrastructure.

## Boundaries

Do not add Qdrant, SQLite, document chunking, retrieval orchestration, keyword search, reranking, or UI.

Keep domain logic out of API handlers. Keep IO and model-backend concerns separate from HTTP projection.

## Engineering Principles

- Prefer simple, explicit design.
- Do not add compatibility patches unless explicitly required by the published API contract.
- Do not hide errors with defensive fallbacks.
- Do not add an abstraction without at least two concrete use cases.
- Keep diffs small and reviewable.

## Commands

- `pytest`
- `ruff check .`
- `python -m compileall app`
- `uvicorn app.main:app --reload --host 127.0.0.1 --port 8100`

## Default Test Backend

Use `EMBEDDING_BACKEND=fake` for tests. Default tests must never download a model.

## Contract

Keep `POST /v1/embeddings` compatible with `retrieval-api`: it returns `data[].embedding` and the documented `vectors` compatibility field.

