# retrieval-api contract

`embedding-api` is an HTTP vector provider for `retrieval-api`. It makes the following guarantees:

1. It provides `GET /v1/health`, `GET /v1/ready`, `GET /v1/info`, `GET /v1/models`, and `POST /v1/embeddings`.
2. Batch embedding output preserves request order, and each `data[index]` corresponds to the same input index.
3. Every successful embedding response returns `model`, `dimension`, and `normalized`.
4. Embeddings are available at `data[].embedding`.
5. The same vectors are available in the compatibility `vectors` field.
6. Callers select retrieval intent with `input_type: query | document`.
7. Prefix rules belong to `embedding-api`; callers must not hard-code model prefixes.
8. The service does not manage collections or documents.
9. The service does not connect to Qdrant.
10. The service does not connect to SQLite.

The API contract version is `embedding-api.v1`.
