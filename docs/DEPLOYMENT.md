# Deployment

## Topology (single host, Docker Compose)

`reverse-proxy` (nginx, unprivileged) -> `frontend`, `api`; `api`/`worker`/`scheduler` -> `postgres`, `redis`, `minio`.
Data services sit on an `internal` network with no route to the internet. Images run as non-root, read-only root filesystem,
all capabilities dropped, `no-new-privileges`, memory limits set. Base images are pinned by tag; Python dependencies by
`requirements.lock`.

| Service | Notes |
| --- | --- |
| `migrate` | one-shot `alembic upgrade head`; `api` and `worker` wait for it. **Replicas never migrate on start.** |
| `api` | stateless (sessions in PostgreSQL, rate limits/budgets in Redis); scale with `docker compose up --scale api=N` after removing the fixed dev port |
| `worker` | all four queues by default; run extra workers with one `-Q` each to scale SMS/AI/export independently |
| `scheduler` | **exactly one**; never scale (duplicate beat processes duplicate jobs) |

## Configuration and secrets

`.env.example` documents every variable. In production set `APP_ENV=production` and inject secrets from a secret manager.
The API **refuses to start** in production when any of these hold: placeholder or `<32`-character secrets, `DEV_SMS_ECHO_ENABLED`,
`COOKIE_SECURE=false`, wildcard CORS, non-HTTPS `AI_BASE_URL`, sandbox payments enabled, sandbox test orders enabled.

Production: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`.

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
database with 12 tables and the probe row intact. Not yet covered: object-storage (MinIO) backup, off-host copies, scheduled
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
