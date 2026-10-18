# The karting "coming soon" game (FastAPI + static canvas game + leaderboard). Single worker on purpose: its
# anti-cheat and rate-limit state lives in process memory (app/service.py). Database URL comes from LANDING_DATABASE_URL
# (sqlite by default). PIP_INDEX_URL can point at a mirror for a slow/blocked PyPI route; it defaults to PyPI.
FROM python:3.12-slim
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10
ARG PIP_INDEX_URL=https://pypi.org/simple
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install --index-url "$PIP_INDEX_URL" -r requirements.txt
COPY . .
EXPOSE 8090
HEALTHCHECK --interval=15s --timeout=4s --start-period=15s --retries=3 \
  CMD ["python","-c","import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/api/health',timeout=3).status==200 else 1)"]
CMD ["sh","-c","alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8090"]
