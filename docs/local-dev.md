# Local development

No Docker installation is required for local development.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Use fake mode for normal development, tests, and smoke checks:

```bash
EMBEDDING_BACKEND=fake \
uvicorn app.main:app --reload --host 127.0.0.1 --port 8100
```

Use the real model only when testing local inference:

```bash
EMBEDDING_BACKEND=sentence-transformers \
EMBEDDING_MODEL=BAAI/bge-m3 \
EMBEDDING_DEVICE=auto \
EMBEDDING_MODEL_CACHE_DIR="$(pwd)/data/models" \
uvicorn app.main:app --reload --host 127.0.0.1 --port 8100
```

Run the checks before committing:

```bash
pytest
ruff check .
python -m compileall app
```

## Windows port exclusions

On Windows, a port can be unavailable even when no process is listening if it
falls inside a system excluded port range. Check excluded TCP ports with:

```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

If `8100` is excluded, run the local server on a different host port:

```powershell
$env:EMBEDDING_BACKEND = "fake"
uvicorn app.main:app --reload --host 127.0.0.1 --port 18100
python scripts\smoke_test.py --base-url http://127.0.0.1:18100
```

The optional real-model test intentionally requires an explicit opt-in:

```bash
RUN_REAL_MODEL_TESTS=1 pytest tests/test_real_model.py
```
