# Local Docker deployment

This service is built and pushed by GitHub Actions. Local machines should pull
the published image and keep model weights in a persistent Docker volume.

Keep the real deployment files on each host, or in a separate infrastructure
repository. The files in `deploy/` are examples for bootstrapping a host.

## Compose layout

Copy the examples into a host-owned deployment directory:

```bash
mkdir -p /opt/agent-infra/embedding-api
cp deploy/docker-compose.example.yml /opt/agent-infra/embedding-api/compose.yml
cp deploy/docker-compose.gpu.example.yml /opt/agent-infra/embedding-api/gpu.yml
cp deploy/watchtower.example.yml /opt/agent-infra/embedding-api/watchtower.yml
cd /opt/agent-infra/embedding-api
```

Set the image owner and optional runtime values in a local `.env` file:

```bash
EMBEDDING_IMAGE=007hikari/embedding-api
EMBEDDING_IMAGE_TAG=latest
EMBEDDING_HOST_PORT=8100
EMBEDDING_DEVICE=auto
EMBEDDING_BATCH_SIZE=4
```

Start the service:

```bash
docker compose -f compose.yml up -d
```

On a GPU host, include the GPU override:

```bash
docker compose -f compose.yml -f gpu.yml up -d
```

Start the service and Watchtower together on hosts that should update
automatically:

```bash
docker compose -f compose.yml -f watchtower.yml up -d
```

On a GPU host, include all three files:

```bash
docker compose -f compose.yml -f gpu.yml -f watchtower.yml up -d
```

Watchtower is configured with `--label-enable` and the `agent-infra` scope, so
it only updates containers that explicitly opt in with matching labels.

If Watchtower should manage several local services, keep its compose file in a
separate host-level deployment directory and reuse the same labels on the
containers that should opt in.

`--scope agent-infra` is a Watchtower grouping filter. With the example files,
Watchtower only manages containers that have both labels:

```yaml
com.centurylinklabs.watchtower.enable: "true"
com.centurylinklabs.watchtower.scope: "agent-infra"
```

Existing containers must be recreated to add Docker labels. Docker does not
allow labels to be added to an already-created container in place.

The Watchtower example sets `DOCKER_API_VERSION=1.44`. This keeps Watchtower
compatible with current Docker Desktop releases that reject very old Docker API
clients.

## Health and readiness

The image healthcheck calls `/v1/health`. This is a liveness check and does not
wait for model preload or first-time model download to complete.

Use `/v1/ready` for service readiness:

```bash
curl http://127.0.0.1:8100/v1/ready
```

If the host maps another port, replace `8100` with the host port.

## Updating

The publish workflow pushes two useful tags:

- `latest` for normal automatic updates.
- `<git-sha>` for exact rollbacks or pinned deployments.

To pin a host to a specific build, edit `EMBEDDING_IMAGE_TAG` in the host `.env`
file:

```bash
EMBEDDING_IMAGE_TAG=<git-sha>
```

Then recreate the service:

```bash
docker compose -f compose.yml -f watchtower.yml up -d embedding-api
```

Use `-f gpu.yml` as well on GPU hosts.

To return to automatic updates, set `EMBEDDING_IMAGE_TAG=latest`.

## Docker Hub access

The simple topology is:

```text
GitHub Actions -> Docker Hub -> each local host
```

If every host can reliably pull from Docker Hub, this is enough.

If pulls are slow, rate-limited, or unavailable from some hosts, put a registry
or pull-through cache on the LAN:

```text
GitHub Actions -> Docker Hub -> LAN registry/cache -> each local host
```

With a private LAN registry, one machine pulls the Docker Hub image and pushes it
to an internal address such as `192.168.1.10:5000/embedding-api:latest`. Other
hosts then set:

```bash
EMBEDDING_IMAGE=192.168.1.10:5000/embedding-api
EMBEDDING_IMAGE_TAG=latest
```

Do this only when Docker Hub access becomes a real operational problem.
