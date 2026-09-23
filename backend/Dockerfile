# syntax=docker/dockerfile:1.7

# ---- builder: resolve and install pinned dependencies into an isolated venv --------------------
FROM python:3.12.7-slim-bookworm AS builder
# true only for the API image: adds the local embedding model libraries (CPU-only PyTorch, about 1 GB) that the
# semantic cache needs. The worker, scheduler and migration job stay small.
ARG EMBEDDINGS=false
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /build
COPY requirements.lock requirements-embeddings.lock ./
RUN pip install --no-deps -r requirements.lock
# The +cpu PyTorch wheel is only published on PyTorch's own index; everything else comes from PyPI as before.
RUN if [ "$EMBEDDINGS" = "true" ]; then \
      pip install --no-deps --default-timeout=180 --retries 8 \
        --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-embeddings.lock; \
    fi
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-deps .

# ---- runtime: no compilers, no pip cache, non-root ---------------------------------------------
FROM python:3.12.7-slim-bookworm AS runtime
RUN groupadd --system --gid 10001 davos \
 && useradd --system --uid 10001 --gid davos --home-dir /app --shell /usr/sbin/nologin davos
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --chown=davos:davos alembic.ini ./
COPY --chown=davos:davos migrations ./migrations
# Default assistant style notes and knowledge files; compose mounts the editable host copies over these.
COPY --chown=davos:davos prompts ./prompts
COPY --chown=davos:davos knowledge ./knowledge
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=4s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request as u, sys; sys.exit(0 if u.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=3).status == 200 else 1)"]
# Uvicorn traps SIGTERM and drains in-flight requests (graceful shutdown); replicas scale via compose/orchestrator.
CMD ["uvicorn", "davos.api.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--timeout-graceful-shutdown", "20"]
