# Task checklist and verification record

Legend: [x] done and verified - [~] partly done (details) - [ ] not started - [!] externally blocked

Verification = what was actually executed. Suite totals: 1564 tests pass (Python 3.12.7 Linux and 3.14.0 Windows), ruff and
mypy --strict clean, 5 import contracts kept.

## Phase 1 - foundation

- [x] **1.1 Repository inspection and planning.** Existing scaffold reviewed (plaintext OTP, hardcoded code, fake metrics,
  `signature == "valid"`, error strings returned as AI answers); backed up to `_legacy/`; rebuilt.
- [x] **1.2 Tooling.** `pyproject.toml` with pinned ranges, `requirements.lock` / `requirements-dev.lock` generated on Linux/3.12,
  ruff, mypy strict, pytest, import-linter. Frontend tooling not touched.
- [x] **1.3 Hexagonal foundation.** shared kernel, ports/adapters, composition root, Unit of Work, architecture tests
  (one class per file, layering, clock discipline, ports are ABCs).
- [x] **1.4 Persistence.** SQLAlchemy 2 async, six Alembic migrations, constraints, real-PostgreSQL test infrastructure,
  drift and reversibility tests.
- [~] **1.5 Docker.** Multi-stage non-root images, compose topology with private data network, migration job, health checks,
  resource limits, pinned images. Verified: image build, `migrate` -> `api`/`worker`/`scheduler` healthy, readiness, non-root, `minio` healthy.
  No `monitoring` profile.
- [~] **1.6 Design system / frontend foundation.** Done 2026-09-21: light premium theme with WCAG-checked tokens, RTL, Vazirmatn +
  Unbounded, shared components, home/FAQ/contact/404 pages, track map traced from a satellite image. Not done: Dana font (licence),
  dashboard/admin/CMS, automated frontend tests (see `LIMITATIONS.md`). Content (phone, hours, phone-only booking rule, FAQ) was
  replaced with facts the owner gave on 2026-09-21; prices, address and clothing remain unconfirmed and are not on the site.
- [~] **1.7 Assistant chat on the site.** Done 2026-09-21: floating chat box (lazy-loaded, sources, feedback, fallback with a link to
  the contact page), two-layer system prompt (fixed rules in code + owner-editable `backend/prompts/assistant_persona.txt`),
  knowledge as `backend/knowledge/*.txt` synced to the database (drafts never quoted), whole-knowledge retrieval while the base is
  small, message wording aligned with the phone-only booking. Verified: 1691 backend tests, and by hand ~35 questions against a
  real provider (GapGPT, `gemma-3-27b-it`). Not done: conversation memory, an evaluation set, admin views (see `AI_ASSISTANT.md`).

- [x] **1.8 Semantic answer cache and conversation memory.** Built 2026-09-21 (all local: sentence-transformers embeddings,
  pgvector, migration `0007`), then the cache half was **retired 2026-09-23** (migration `0008`): the embedding model competed
  for CPU/RAM in the API process and degraded ordinary answers. Its code is kept on the `feature/semantic-cache` branch, not on
  `main`. The follow-up conversation memory (Redis, no embeddings) stays and is unaffected.

## Phase 2 - identity, CMS, public site

- [x] **2.1 Customer authentication.** OTP (HMAC digest, expiry, attempt lock, cooldown, mobile+IP rate limits), sessions
  (hashed tokens, list, revoke, IDOR-safe), CSRF, hardened cookie, production config guard. Concurrency tests pass.
- [ ] **2.2 Administrator authentication.**
- [ ] **2.3 CMS and media.**
- [ ] **2.4 Public pages.**
- [ ] **2.5 Contact and tickets.**

## Phase 3 - customer club and dashboards

- [~] **3.1 Profiles and account settings.** Sessions/devices done; profile, preferences, mobile change, deletion not.
- [x] **3.2 Loyalty ledger and tiers.** Append-only (DB trigger), idempotent by source event, concurrency-safe spend, reversals,
  expiry (FIFO-equivalent), tier ladder. 12-way duplicate award and 30-way redemption race tested.
- [~] **3.3 Discounts and benefits.** Deterministic discount engine (stacking, caps, validity, scope, snapshot). No storage/admin
  for permanent discounts or coupons; no birthday/referral/campaigns.
- [ ] **3.4 Customer dashboard.** (no UI; APIs exist only for sessions, assistant, payments, booking return)
- [ ] **3.5 Administration panel.**
- [ ] **3.6 Reporting and exports.**

## Phase 4 - integrations

- [x] **4.1 Outbox and jobs.** Atomic outbox, `SKIP LOCKED` relay, backoff+jitter, dead-letter, Celery with four isolated queues,
  late acks, one scheduler. Bug fixed: loop-bound resources in tasks.
- [~] **4.2 SMS.** `SmsGatewayPort` + recording adapter used for OTP. No real provider, templates, tracking or consent rules.
- [~] **4.3 Booking contracts.** Signed webhook (window, rotation, raw-body HMAC), inbox dedupe, out-of-order, failure tracking
  and reprocessing, verified return page, feature flag. Missing: inquiry/reconciliation polling, OIDC handoff, redirect allow-list.
- [~] **4.4 Zarinpal.** State machine, server-side amounts, exclusive verification, exactly-once success under concurrency,
  DB guard against double payment, UNKNOWN + reconciliation, sandbox order path, API. [!] Live sandbox unverified; no refunds.
- [~] **4.5 FAQ search and AI.** Retrieval, normalisation, grounding, injection controls, budgets, breaker/bulkhead, fallback,
  consent/retention, feedback. Missing: admin views, FAQ drafts from questions, live provider test.

## Phase 5 - verification and delivery

- [~] **5.1 SEO audit.** Not applicable yet (no pages). API security headers verified.
- [~] **5.2 Security audit.** Verified for what exists: OTP/session/CSRF/IDOR/webhook/payment/AI controls, log redaction, secrets
  guard. No upload, admin or XSS surface exists yet; no external penetration test.
- [ ] **5.3 Scalability and observability.** Shared state and worker separation exist; no metrics, tracing, dashboards or load test.
- [~] **5.4 Deployment and recovery.** Compose, controlled migrations, graceful shutdown settings, verified backup/restore of
  PostgreSQL, CI file (not executed). Object storage backup absent.
- [ ] **5.5 Full-system acceptance (Playwright).**
- [~] **5.6 Documentation.** README, architecture (with diagrams), AI design, integrations (payloads), testing, deployment,
  limitations. No OpenAPI client generation yet.
