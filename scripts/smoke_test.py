from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def fetch(url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    body = None if payload is None else json.dumps(payload).encode()
    request = Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read())
    except HTTPError as error:
        raise RuntimeError(f"{url} returned HTTP {error.code}: {error.read().decode()}") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal embedding-api HTTP smoke test.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8100")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    health = fetch(f"{base_url}/v1/health")
    info = fetch(f"{base_url}/v1/info")
    embeddings = fetch(f"{base_url}/v1/embeddings", {"input": "embedding-api smoke test"})

    if health.get("status") != "ok":
        raise RuntimeError("health endpoint did not report ok")
    if not info.get("models"):
        raise RuntimeError("info endpoint did not return a model")
    if len(embeddings.get("data", [])) != 1:
        raise RuntimeError("embedding endpoint did not return one vector")
    print("smoke test passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"smoke test failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
