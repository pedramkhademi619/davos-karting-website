# Davos Karting (کارتینگ داوس)

Backend for the Davos Karting website: a **modular monolith with hexagonal architecture** (FastAPI, SQLAlchemy 2,
PostgreSQL, Redis, Celery). The web app and admin panel are **not built yet** (see [Status](#status)).

## What exists and works

| Area | State |
| --- | --- | 
| Customer login (mobile + SMS OTP), server-side sessions, CSRF, device list / logout | implemented, tested |
| FAQ assistant (retrieval-grounded AI, Persian search, guardrails, budgets, fallback) and its chat box on the site | implemented, tested; tried by hand against one real provider (see [docs/AI_ASSISTANT.md](docs/AI_ASSISTANT.md)) |
| Loyalty: append-only points ledger, tiers, deterministic discount engine | implemented, tested (no admin UI, no coupon/referral storage yet) |
| Payments: state machine, Zarinpal adapter, callback verification, reconciliation | implemented, tested against the documented contract; **live sandbox not verified** |
| Booking integration: signed webhooks, replay/duplicate/out-of-order handling, verified return page | implemented, tested; OIDC SSO handoff **not implemented** |
| Transactional outbox, Celery worker + single scheduler, isolated queues | implemented, tested (no event consumers registered yet) |
| Docker Compose stack, controlled migration job, non-root images, backup/restore scripts | implemented; data services, migrate, api, worker, scheduler and minio verified healthy locally |
| Public website | **partly built.** Light, premium pages (home with the track map traced from a satellite image, `/faq`, `/contact`) and the assistant chat box, the only thing that calls the API; no dead links. Phone, hours, booking rule and FAQ come from the owner (booking is by phone); prices, e-mail and street address are not shown because they are unconfirmed. The map's scenery is a simplified redraw and it is not a survey. See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) |
| Customer dashboard, admin panel, CMS, SEO | **not implemented** |

The precise, per-task record is in [docs/TASKS.md](docs/TASKS.md); everything not done or not verified is listed in
[docs/LIMITATIONS.md](docs/LIMITATIONS.md).

## Quick start

```bash
cp .env.example .env            # development placeholders only
docker compose up --build       # postgres, redis, migrate (one-shot), api, worker, scheduler, frontend, proxy, minio
```

* Site and API behind the proxy: `http://localhost:${HTTP_PORT}` (default 80; if another program holds port 80, set e.g.
  `HTTP_PORT=8088` in `.env`). The proxy hides the docs and `/api/v1/health/ready`.
* API directly: `http://127.0.0.1:8000/api/docs` (development only; Swagger UI loads its scripts from a CDN, so it needs internet)
  - readiness: `http://127.0.0.1:8000/api/v1/health/ready`
* To read OTP codes locally set `DEV_SMS_ECHO_ENABLED=true` in `.env` (rejected in production).
* To switch the site's chat assistant on, set `AI_BASE_URL`, `AI_API_KEY` and `AI_MODEL` in `.env` and run `docker compose up -d api`.
  Its tone lives in `backend/prompts/assistant_persona.txt` and its facts in `backend/knowledge/*.txt` (both editable, Persian
  guide in `backend/knowledge/README.md`). Details: [docs/AI_ASSISTANT.md](docs/AI_ASSISTANT.md).
* Backend without Docker: see [docs/TESTING.md](docs/TESTING.md).

## Repository layout

```text
backend/
  src/davos/
    shared_kernel/      Entity, AggregateRoot, DomainEvent, Money (integer IRR), Clock/UnitOfWork/RateLimiter ports, errors
    modules/<module>/   identity | assistant | loyalty | payments | booking | notifications
      domain/           pure business rules (no framework imports; enforced)
      application/      use cases + ports (abstract interfaces)
      adapters/         SQLAlchemy repositories, HTTP clients, security helpers
    platform/           settings, database/UoW/outbox, Redis rate limiter, circuit breaker, log redaction
    composition/        the only place that binds ports to adapters (ApplicationContainer)
    api/                FastAPI app, versioned routers (/api/v1), schemas, middleware, error handling
    worker/             Celery app, tasks, queue definitions
  migrations/           Alembic (one migration per change; drift and reversibility are tested)
  tests/                unit | integration (real PostgreSQL + Redis) | architecture
docs/                   architecture, AI design, integrations, testing, deployment, tasks, limitations
nginx/  scripts/  docker-compose*.yml  .env.example
```

## Engineering rules (enforced by tests, not by convention)

* **One class per file, named after the class** - `tests/architecture/test_one_class_per_file.py`.
* **Domain layers import no framework**, application layers import no infrastructure, modules never import each other,
  nothing imports the composition root or API - `import-linter` contracts (`pyproject.toml`) run inside the test suite.
* Domain and application code never read the wall clock (a `Clock` is injected) and the domain is synchronous and I/O-free.
* Every ORM model is registered for Alembic, and models and migrations must not drift (`alembic check` is a test).
* `ruff` and `mypy --strict` are clean; dependencies are pinned in `requirements*.lock`; images are pinned by tag.

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before adding a module.
