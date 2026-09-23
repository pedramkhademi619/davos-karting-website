# Testing

## Layers

| Layer | Location | What it proves |
| --- | --- | --- |
| Unit | `tests/unit` | domain rules, use cases with in-memory fakes, adapters with recorded HTTP shapes (`respx`) |
| Integration | `tests/integration` | real **PostgreSQL 16** (schema built by Alembic) and real **Redis 7**: constraints, row locks, concurrency, outbox, HTTP API through ASGI |
| Architecture | `tests/architecture` | one class per file, import contracts, no wall clock in domain/application, ports are ABCs, models registered |

There is no SQLite fallback: PostgreSQL-specific behaviour (row locks, `ON CONFLICT`, partial indexes, triggers, `pg_trgm`,
pgvector's HNSW index and iterative scans) is
part of what is tested.

## Run

```bash
# 1. infrastructure for the integration tests
docker build -t davos-postgres:16.4-pgvector0.8.0 postgres      # postgres:16.4-alpine + the pgvector extension
docker run -d --name davos-pg-test    -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=davos_test -p 54329:5432 davos-postgres:16.4-pgvector0.8.0
docker run -d --name davos-redis-test -p 63799:6379 redis:7.4-alpine

# 2. backend
cd backend
python -m venv .venv && . .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.lock && pip install --no-deps -e .
pytest                                                # everything
pytest tests/unit tests/architecture                  # no containers needed
ruff check src tests && ruff format --check src tests
mypy src
lint-imports
```

Override endpoints with `TEST_DATABASE_URL` / `TEST_REDIS_URL` (CI does).

## Recorded results (this repository, 2026-09-21)

* `pytest`: **1582 passed** on Windows / Python 3.14 (`pytest` and `pytest --cov`) **and** in a `python:3.12.7-slim-bookworm`
  container (the production runtime) using the pinned `requirements-dev.lock`, against PostgreSQL 16.4 and Redis 7.4.
* Line coverage **99%** (`pytest --cov=davos`, 4039 statements, 56 missed). Coverage shows what ran, not how good the assertions are.
* `ruff check` / `ruff format --check`: clean. `mypy --strict`: clean (375 files). `import-linter`: 5 contracts kept, 0 broken
  (both also re-run on Linux / 3.12.7).
* `alembic check`: models and migrations in sync; `downgrade base` and `upgrade head` both succeed on a scratch database.
* Backup, then restore into a scratch database: migration `0006` and 12 tables, identical to the live database.
* `pip-audit -r requirements.lock --strict` (Python 3.12 Linux container): no known vulnerabilities on 2026-09-20.
* Bugs found by tests/running the stack (and fixed, with regression tests): in-memory rate limiter pruned long windows;
  Celery tasks shared a loop-bound container; uvicorn's access log bypassed the log-masking handler and wrote raw phone numbers
  and query-string tokens; the Celery worker/beat used their own unmasked log format; the masking patterns missed
  `token=`/`secret=`/`Authority=` values and mangled long numbers that merely contained a mobile-shaped digit run; the nginx
  access log recorded full query strings. The last one has no automated test: it was found and verified against the running stack
  only (send a request with a phone-shaped query value, confirm the proxy log has the path only).

Not executed: Playwright / browser tests (no frontend), load tests, live provider calls.
