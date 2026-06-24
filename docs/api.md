# API reference

All production endpoints use the `/v1` prefix. JSON error responses have this shape:

```json
{
  "error": {
    "code": "MODEL_NOT_FOUND",
    "message": "Model not found: example/model",
    "details": {}
  }
}
```

## System endpoints

| Endpoint | Purpose | Authentication |
| --- | --- | --- |
| `GET /v1/health` | Process liveness; never loads a model | Never required |
| `GET /v1/ready` | Model readiness | Optional by configuration |
| `GET /v1/info` | Runtime and model metadata | Required when API key auth is enabled |
| `GET /v1/models` | Configured model list | Required when API key auth is enabled |
| `GET /v1/models/{model_name}` | One model's metadata; model names may contain `/` | Required when API key auth is enabled |

`/v1/health` returns HTTP 200 whenever the HTTP process is alive. `/v1/ready` returns HTTP 503 with `status: not_ready` until a lazy model has loaded or if preload failed.

## `POST /v1/embeddings`

```json
{
  "model": "BAAI/bge-m3",
  "input": ["第一段文本", "second text"],
  "input_type": "document",
  "normalize": true,
  "truncate": true,
  "return_usage": true
}
```

`model` is optional and defaults to the configured model. `input` accepts either one string or an array of strings. `input_type` is `query` or `document`; the service applies any model-specific prefix policy internally. BGE-M3 receives no forced prefix.

The response preserves input order:

```json
{
  "object": "list",
  "model": "BAAI/bge-m3",
  "dimension": 1024,
  "normalized": true,
  "input_type": "document",
  "data": [
    {"object": "embedding", "index": 0, "embedding": [0.01, -0.02]}
  ],
  "usage": {"prompt_tokens": 15, "total_tokens": 15, "input_count": 1},
  "vectors": [[0.01, -0.02]]
}
```

`data[].embedding` is the current contract. `vectors` is retained for earlier `retrieval-api` clients and new clients should not depend on it.

## Authentication

Set both `EMBEDDING_REQUIRE_API_KEY=true` and `EMBEDDING_API_KEY` to require:

```http
Authorization: Bearer your-token
```

`/v1/health` remains public. `/v1/ready` remains public unless `EMBEDDING_REQUIRE_API_KEY_FOR_READY=true`.

## Error codes

| HTTP status | Codes |
| --- | --- |
| 400 | `INVALID_REQUEST`, `INPUT_TOO_LONG`, `BATCH_TOO_LARGE` |
| 401 | `UNAUTHORIZED` |
| 404 | `MODEL_NOT_FOUND` |
| 503 | `MODEL_NOT_READY`, `MODEL_LOAD_FAILED`, `DEVICE_UNAVAILABLE` |
| 500 | `EMBEDDING_FAILED`, `INTERNAL_ERROR` |
