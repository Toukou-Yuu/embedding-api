FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EMBEDDING_HOST=0.0.0.0 \
    EMBEDDING_PORT=8100 \
    EMBEDDING_MODEL_CACHE_DIR=/models

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir . && mkdir -p /models

VOLUME ["/models"]
EXPOSE 8100

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
