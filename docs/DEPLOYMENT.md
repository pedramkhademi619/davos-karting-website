# Deployment

## Topology (single host, Docker Compose)

`reverse-proxy` (nginx, unprivileged) -> `frontend`, `api`; `api`/`worker`/`scheduler` -> `postgres`, `redis`.
Data services sit on an `internal` network with no route to the internet. Images run as non-root, read-only root filesystem,
all capabilities dropped, `no-new-privileges`, memory limits set. Base images are pinned by tag; Python dependencies by
`requirements.lock`.

| Service | Notes |
| --- | --- |
| `migrate` | one-shot `alembic upgrade head`; `api` and `worker` wait for it. **Replicas never migrate on start.** |
| `frontend` | `FRONTEND_REPLICAS` (default 3) Next.js processes; every page is rendered per request (it carries its own CSP nonce), about 25-35 pages/s per replica |
| `api` | `API_WORKERS` (default 4) uvicorn worker processes; stateless (sessions in PostgreSQL, rate limits/budgets in Redis); one worker does the start-up work (knowledge seed on an empty database, first admin) under a PostgreSQL advisory lock |
| `worker` | all four queues by default; run extra workers with one `-Q` each to scale SMS/AI/export independently |
| `scheduler` | **exactly one**; never scale (duplicate beat processes duplicate jobs) |

## Configuration and secrets

One source per value:

| What | Where it lives | Who reads it |
| --- | --- | --- |
| Deployment settings, limits, timeouts, provider addresses, secrets | `.env` (complete working example: `.env.example`) | backend: `AppSettings` (`backend/src/davos/platform/settings/app_settings.py`) only declares them, with no values or defaults; the composition root (`PolicyFactory`, `ApplicationContainer`) hands the values to the modules, which never read the environment |
| Public values baked into the web app (site addresses, `CONTACT_PHONE`, `VENUE_LATITUDE`/`VENUE_LONGITUDE`) | the same `.env` | `docker-compose.yml` passes them as build arguments (`frontend/Dockerfile`, `frontend/src/lib/urls.ts`, `frontend/src/lib/venue.ts`); rebuild the frontend after changing them |
| Prices, karts per session, closed days, hold time, online booking on/off | admin panel, booking settings | backend and site at run time (the assistant within `ASSISTANT_BOOKING_FACTS_CACHE_SECONDS`) |
| The owner's riding rules (ages, height, seats) | domain code (`EligibilityRules`) and `backend/knowledge` | backend; a test keeps the two in step |

No value is written in code, and there are no fallbacks: a setting missing from `.env` stops the API (or the web app's
build) at start-up with its name, and the error never prints the other values. The API, worker, scheduler and migration
job load the whole `.env` (`env_file` in `docker-compose.yml`); compose itself only builds the containers' database and
Redis addresses from the passwords in `.env`, and requires every variable it uses. `.env.example` is a complete working
development configuration in the order of `AppSettings`; `backend/tests/unit/platform/test_env_example.py` fails when a
setting is missing from it, unused or commented out, and the tests run on it (never on a developer's `.env`).

In production set `APP_ENV=production` and inject secrets from a secret manager.
The API **refuses to start** in production when any of these hold: placeholder or `<32`-character secrets, `DEV_SMS_ECHO_ENABLED`,
`COOKIE_SECURE=false`, wildcard CORS, non-HTTPS `AI_BASE_URL`, sandbox payments enabled, sandbox test orders enabled.

Production: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`.

## Answer cache model (one download per server)

The assistant's answer cache finds earlier questions with the same meaning using a small embedding model that runs inside each
API process (no network call at run time). Its files are not in git: fetch them once on every machine that runs the API, from
the repository root, and the compose file mounts `backend/models` read-only into the API container:

```bash
backend/.venv/Scripts/python.exe -m davos.tools.fetch_embedding_model backend/models/paraphrase-multilingual-minilm
```

It downloads three public files (about 124 MB) from pinned commits and refuses any whose SHA-256 differs. Without the folder the
API starts normally with the cache off and every question goes to the language model. Each API worker process needs about
310 MB with the model loaded (`API_WORKERS` x that, within `API_MEMORY_LIMIT`). To run offline, copy the folder from another
machine. Settings: `SEMANTIC_CACHE_*` in `.env.example`; method and measurements: [ASSISTANT_EVALUATION.md](ASSISTANT_EVALUATION.md).

## Hosts: main site and booking subdomain

One deployment serves two hostnames through the same nginx and web app:

| Host | Pages | Example |
| --- | --- | --- |
| main (`PUBLIC_BASE_URL`) | home, FAQ, contact, assistant, `/admin` | `https://davoskarting.ir` |
| booking (`BOOKING_BASE_URL`) | booking page (at `/`), sign-in, the customer's tickets, payment result | `https://booking.davoskarting.ir` |

`src/proxy.ts` in the web app sends each path to its host (`/booking`, `/account`, `/login`, `/payment/*` on the main host
redirect to the subdomain; FAQ, contact and admin on the subdomain redirect back). The bank's callback and the redirect after
paying go to the booking host, because the customer's sign-in cookie is scoped to it. Both addresses are always trusted
origins for the API's CSRF origin check. Leave `BOOKING_BASE_URL` empty to keep everything on one host.

Before launch: DNS `A` records for both names, one TLS certificate that covers both (terminated in front of nginx), both URLs
with `https://` in `.env`, then rebuild the web app (`docker compose build frontend`: the addresses are baked in at build time).
Tell the bank the server's public IP (Behpardakht only accepts calls from registered IPs) and, if they ask, the callback
domain `booking.<domain>`.

## Busy days: what was measured

Local stack (Docker Desktop, 12 cores), load generated inside the Docker network, 2026-09-25:

* 40 signed-in customers holding karts in the **same** session at the same moment: exactly one session's worth sold (6
  singles + the double), 36 refused with `session_full`, never oversold; every customer had an answer within 0.9 s.
* The seat map, calendar and booking facts every visitor polls are answered from nginx's 2-second cache (100 % of those
  requests in the test), so a crowd does not reach the API or the database.
* Pages: ~25-35 per second per web replica (the home page is ~140 KB; the track map is drawn in the browser). Raise
  `FRONTEND_REPLICAS` with the server's cores; raise `API_WORKERS` if the API's CPU becomes the limit.
* Edge limits are per IP and generous (many mobile customers share one carrier IP); the real limits are per mobile number.

## Migrations (expand / contract)

Ship schema changes in two releases: (1) *expand* - add nullable columns/tables/indexes, code tolerates both shapes;
(2) *contract* - remove the old shape once no running version uses it. `0003_outbox_dead_letter` is an example of an expand step.
CI-level guards: `alembic check` (no drift) and a downgrade/upgrade round-trip test.

## Backup and restore

```bash
sh scripts/backup-postgres.sh ./backups                     # custom-format dump, 14-day retention (BACKUP_RETENTION_DAYS)
sh scripts/restore-postgres.sh backups/davos-<stamp>.dump   # restores into NEW database davos_restore_check, prints a summary
```

Verified on this repository's compose stack: a dump of a database at migration 0006 (with a probe row) restored into a fresh
database with 12 tables and the probe row intact. Not yet covered: off-host copies, scheduled
runs, restore-time targets. Schedule the script from the host and copy dumps off-machine.

## Scaling path

Compose is the first stage. Next: several API/worker hosts behind a load balancer (state is already shared), PgBouncer in
transaction mode in front of PostgreSQL (pool per replica x replicas must stay below `max_connections`; keep prepared-statement
caching off for asyncpg when doing so), managed Redis/PostgreSQL. Kubernetes is optional, not required.

## Shutdown

`uvicorn --timeout-graceful-shutdown 20` and compose `stop_grace_period` (30 s API, 60 s worker) let in-flight requests/tasks
finish; Celery acknowledges tasks late so a killed worker never loses one.

## CI

`.github/workflows/ci.yml` runs lint, format check, `mypy`, import contracts, the full test suite against PostgreSQL/Redis
service containers, a backend image build and `pip-audit`. **The workflow has not been executed** (no repository host here);
its commands were run locally.
