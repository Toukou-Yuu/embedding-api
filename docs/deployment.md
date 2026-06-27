# Docker deployment

Build on a Linux host or in GitHub Actions:

```bash
docker build -f docker/Dockerfile -t "$DOCKERHUB_USERNAME/embedding-api:latest" .
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
  "$DOCKERHUB_USERNAME/embedding-api:latest"
```

On Windows, host port `8100` may be unavailable because it falls inside a system
excluded port range. Check with:

```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

If `8100` is excluded, keep the container port unchanged and map another host
port:

```powershell
docker run -d `
  --name embedding-api `
  --restart unless-stopped `
  -p 18100:8100 `
  -v embedding-models:/models `
  -e EMBEDDING_HOST=0.0.0.0 `
  -e EMBEDDING_PORT=8100 `
  -e EMBEDDING_MODEL_CACHE_DIR=/models `
  007hikari/embedding-api:latest
```

Use `http://127.0.0.1:18100` as the local base URL for that mapping.

The Dockerfile never downloads BGE-M3 during image build. Model data is populated on the first successful runtime load, or an operator can pre-populate the mounted `/models` volume.

For NVIDIA GPU deployment, use `--gpus all` and see [gpu-deployment.md](gpu-deployment.md) for preflight checks and GPU-specific examples.

The GitHub Actions publish workflow builds `$DOCKERHUB_USERNAME/embedding-api:latest` and `$DOCKERHUB_USERNAME/embedding-api:<git-sha>` when Docker Hub credentials are configured as `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`.

For Docker Compose and Watchtower-based local auto-update examples, see
[local-docker-deployment.md](local-docker-deployment.md).
