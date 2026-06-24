# Docker deployment

Build on a Linux host or in GitHub Actions:

```bash
docker build -f docker/Dockerfile -t toukouyuu/embedding-api:latest .
```

Run with a persistent model-cache volume:

```bash
docker run -d \
  --name embedding-api \
  --restart unless-stopped \
  -p 8100:8100 \
  -v embedding-models:/models \
  -e EMBEDDING_HOST=0.0.0.0 \
  -e EMBEDDING_PORT=8100 \
  -e EMBEDDING_MODEL_CACHE_DIR=/models \
  toukouyuu/embedding-api:latest
```

The Dockerfile never downloads BGE-M3 during image build. Model data is populated on the first successful runtime load, or an operator can pre-populate the mounted `/models` volume.

The GitHub Actions publish workflow builds `toukouyuu/embedding-api:latest` and `toukouyuu/embedding-api:<git-sha>` when Docker Hub credentials are configured as `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`.
