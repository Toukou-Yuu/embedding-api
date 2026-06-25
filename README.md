# embedding-api

`embedding-api` is a standalone HTTP service that turns text into embedding vectors for local agent infrastructure.

It is deliberately narrow: it owns model loading and vector generation only. It does not save vectors, manage collections, split documents, access Qdrant or SQLite, perform keyword/hybrid search, rerank, or provide a UI.

`retrieval-api` is an HTTP client of this service. It owns document ingestion, storage, and retrieval orchestration; `embedding-api` has no dependency on it.

## Local development without Docker

Python 3.11 or newer is required. Docker is not needed for local development or tests.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the fake backend first. It downloads no model and is the default test backend:

```bash
export EMBEDDING_BACKEND=fake
export EMBEDDING_HOST=127.0.0.1
export EMBEDDING_PORT=8100

uvicorn app.main:app --reload --host 127.0.0.1 --port 8100
```

Run the real BGE-M3 model when the local machine is ready to download it:

```bash
export EMBEDDING_BACKEND=sentence-transformers
export EMBEDDING_MODEL=BAAI/bge-m3
export EMBEDDING_DEVICE=auto
export EMBEDDING_MODEL_CACHE_DIR="$(pwd)/data/models"

uvicorn app.main:app --reload --host 127.0.0.1 --port 8100
```

`auto` selects CUDA, then Apple MPS, then CPU. An explicit unavailable `cuda` or `mps` configuration fails clearly at startup.

## API example

```bash
curl http://127.0.0.1:8100/v1/health

curl http://127.0.0.1:8100/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "BAAI/bge-m3",
    "input": ["第一段文本", "second text"],
    "input_type": "document",
    "normalize": true
  }'
```

The embedding response contains the current contract field, `data[].embedding`, and the `vectors` compatibility field for earlier `retrieval-api` clients. See [docs/api.md](docs/api.md) and [docs/contract.md](docs/contract.md).

## Tests and checks

```bash
pytest
ruff check .
python -m compileall app
python scripts/smoke_test.py --base-url http://127.0.0.1:8100
```

Default tests use the fake backend and do not download BGE-M3. To explicitly run the real-model test:

```bash
RUN_REAL_MODEL_TESTS=1 pytest tests/test_real_model.py
```

## Docker deployment

Build and run on a Linux host:

```bash
docker build -f docker/Dockerfile -t "$DOCKERHUB_USERNAME/embedding-api:latest" .
docker run --rm -p 8100:8100 \
  -v embedding-models:/models \
  -e EMBEDDING_HOST=0.0.0.0 \
  -e EMBEDDING_MODEL_CACHE_DIR=/models \
  "$DOCKERHUB_USERNAME/embedding-api:latest"
```

The image never includes model weights. The first successful runtime load stores weights in the mounted `/models` volume. See [docs/deployment.md](docs/deployment.md).

## Environment variables

| Variable | Default | Meaning |
| --- | --- | --- |
| `EMBEDDING_HOST` | `127.0.0.1` | HTTP bind address |
| `EMBEDDING_PORT` | `8100` | HTTP bind port |
| `EMBEDDING_BACKEND` | `sentence-transformers` | `sentence-transformers` or `fake` |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Default model name |
| `EMBEDDING_DEVICE` | `auto` | `auto`, `cpu`, `cuda`, or `mps` |
| `EMBEDDING_PRELOAD` | `true` | Load the model during startup |
| `EMBEDDING_BATCH_SIZE` | `16` | Per-request backend encode chunk size |
| `EMBEDDING_MAX_BATCH_SIZE` | `32` | Maximum inputs per API request |
| `EMBEDDING_MAX_INPUT_CHARS` | `12000` | Maximum characters per input |
| `EMBEDDING_MAX_LENGTH` | `8192` | Maximum token length passed to the model |
| `EMBEDDING_NORMALIZE` | `true` | Default model metadata normalization setting |
| `EMBEDDING_RECOMMENDED_DISTANCE` | `Cosine` | Reported recommended vector distance |
| `EMBEDDING_MODEL_CACHE_DIR` | `./data/models` | Local model cache; `/models` in Docker |
| `EMBEDDING_ENCODE_CONCURRENCY` | `1` | Concurrent inference limit |
| `EMBEDDING_FAKE_DIMENSION` | `16` | Fake-backend vector dimension |
| `EMBEDDING_API_KEY` | empty | Bearer token when authentication is enabled |
| `EMBEDDING_REQUIRE_API_KEY` | `false` | Require the token for `/v1/*` except health |
| `EMBEDDING_REQUIRE_API_KEY_FOR_READY` | `false` | Also require the token for ready |
| `LOG_LEVEL` | `INFO` | Structured logging level |

## FAQ

**Does embedding-api save vectors?** No. It generates vectors only.

**Does embedding-api depend on retrieval-api?** No. `retrieval-api` is an `embedding-api` client.

**Can I develop without Docker?** Yes. Use a Python virtual environment and run Uvicorn directly.

**Where are model files stored?** Locally the default is `./data/models`; in Docker it is the `/models` volume.
