# NVIDIA GPU deployment

`embedding-api` uses PyTorch through `sentence-transformers`. GPU support depends on
three separate layers being correct:

1. The host NVIDIA driver can see the GPU.
2. Docker exposes the GPU to the container.
3. The PyTorch wheel inside the image supports the GPU compute capability.

The service should be started with `EMBEDDING_DEVICE=auto` or
`EMBEDDING_DEVICE=cuda` for GPU inference. Do not set `EMBEDDING_DEVICE=cpu` for a
GPU deployment.

## GPU architecture policy

PyTorch CUDA wheels are fat binaries: one wheel can support multiple NVIDIA
compute capabilities. Do not assume a Docker tag supports a GPU just because it
contains CUDA libraries. Verify the tag on each target machine:

```bash
docker run --rm --gpus all --entrypoint python 007hikari/embedding-api:latest -c "
import json
import torch
print(json.dumps({
    'torch': torch.__version__,
    'torch_cuda': torch.version.cuda,
    'cuda_available': torch.cuda.is_available(),
    'device_count': torch.cuda.device_count(),
    'device_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    'device_capability': torch.cuda.get_device_capability(0) if torch.cuda.is_available() else None,
    'arch_list': torch.cuda.get_arch_list() if torch.cuda.is_available() else [],
}, ensure_ascii=False))
"
```

The GPU is suitable for this image when `cuda_available` is `true` and the
device capability appears in `arch_list`. For example:

| GPU | Expected capability | Deployment note |
| --- | --- | --- |
| GeForce GTX 1660 Ti 6GB | `sm_75` | Use a CUDA image whose `arch_list` includes `sm_75`; start with small batches such as `EMBEDDING_BATCH_SIZE=1` or `4` because VRAM is limited. |
| GeForce RTX 5060 Ti 16GB | `sm_120` | Use a CUDA image whose `arch_list` includes `sm_120`; current CUDA 13 PyTorch builds are the intended target for this architecture. |

If a future published tag changes its PyTorch build, re-run the probe before
deploying it on either machine.

## Windows Docker Desktop

On Windows, use Docker Desktop with the WSL2 backend and an NVIDIA driver that
supports CUDA in WSL. Check the host first:

```powershell
nvidia-smi
docker info --format "{{json .Runtimes}}"
```

`docker info` should include an `nvidia` runtime. Then check GPU passthrough:

```powershell
docker run --rm --gpus all --entrypoint nvidia-smi 007hikari/embedding-api:latest
```

Run the service with GPU access:

```powershell
docker rm -f embedding-api
docker run -d `
  --name embedding-api `
  --restart unless-stopped `
  --gpus all `
  -p 18100:8100 `
  -v embedding-models:/models `
  -e EMBEDDING_HOST=0.0.0.0 `
  -e EMBEDDING_PORT=8100 `
  -e EMBEDDING_MODEL_CACHE_DIR=/models `
  -e EMBEDDING_MODEL=BAAI/bge-m3 `
  -e EMBEDDING_DEVICE=auto `
  -e EMBEDDING_BATCH_SIZE=4 `
  -e EMBEDDING_PRELOAD=true `
  007hikari/embedding-api:latest
```

Use `-p 18100:8100` only when Windows excludes host port `8100`; otherwise
`-p 8100:8100` is fine.

## Linux Docker host

On Linux, install the NVIDIA driver and NVIDIA Container Toolkit, then configure
Docker to use the NVIDIA runtime:

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Verify the runtime before starting the service:

```bash
nvidia-smi
docker run --rm --gpus all --entrypoint nvidia-smi 007hikari/embedding-api:latest
```

Run the service:

```bash
docker rm -f embedding-api || true
docker run -d \
  --name embedding-api \
  --restart unless-stopped \
  --gpus all \
  -p 8100:8100 \
  -v embedding-models:/models \
  -e EMBEDDING_HOST=0.0.0.0 \
  -e EMBEDDING_PORT=8100 \
  -e EMBEDDING_MODEL_CACHE_DIR=/models \
  -e EMBEDDING_MODEL=BAAI/bge-m3 \
  -e EMBEDDING_DEVICE=auto \
  -e EMBEDDING_BATCH_SIZE=4 \
  -e EMBEDDING_PRELOAD=true \
  007hikari/embedding-api:latest
```

For a 6GB GPU, lower `EMBEDDING_BATCH_SIZE` first if the model loads but
embedding requests fail with CUDA out-of-memory errors.

## Runtime verification

After startup, the ready endpoint must report CUDA:

```bash
curl http://127.0.0.1:8100/v1/ready
```

Expected field:

```json
{"device": "cuda"}
```

If it reports `cpu`, the container either was not started with `--gpus all`, was
started with `EMBEDDING_DEVICE=cpu`, or Docker could not expose the NVIDIA
runtime to the container.
