# Limitations, gaps and external blockers

Nothing below is claimed as delivered.

## Launch-ready work (2026-09-25): what is and is not verified

* **Verified locally**: online booking on the booking subdomain end to end in a browser (SMS-code sign-in with the code from
  the development log, seat map, hold, ticket with countdown, release, profile save), host routing and redirects between the
  two hosts, the CSP nonce, the edge cache, 40 simultaneous holds on one session never overselling (and the backend tests for
  every payment race), page and API throughput (docs/DEPLOYMENT.md).
* **Not verified against the real services**: Bank Mellat (no terminal credentials yet; the flow is covered by tests with a
  scripted gateway), Kavenegar (development uses the recording gateway), the production TLS/DNS setup for two hosts.
* **Admin panel UI**: every screen type-checks and the admin API has integration tests, but the screens were not clicked
  through with a signed-in account here (the owner creates the first account via `ADMIN_BOOTSTRAP_*`).
* **Counter app is separate**: `D:\Davos\davoos-karting-booking` does not talk to the website. Karts sold at the counter must be
  entered in the admin panel ("ثبت فروش حضوری") or the website can sell them again.
* **Refunds**: a paid online reservation cancelled by staff is not refunded automatically; refund from the bank's panel.

## Not implemented (in scope of the original brief)

* **Web application** beyond three marketing pages and the assistant chat: customer dashboard, admin panel at `/admin`, login,
  Dana font (licensing), Playwright. `frontend/` is a Persian RTL site (home, `/faq`, `/contact`) whose only API call is the
  assistant chat (`POST /api/v1/assistant/ask` and its feedback endpoint, same origin through the proxy).
  It was redesigned on 2026-09-21 as a **light, premium** theme (ivory canvas, ink type, the yellow of the track's terrace as the
  only accent, WCAG AA checked). The price packages and the placeholder "services" were removed at the owner's request.
  * **Verified** (production image, through the proxy; the layout checks in this bullet predate the phone-booking content change,
    after which only links, page text, the 375 px header and the chat widget were re-checked): every internal link answers 200 (the
    old `/booking`, `/login`, `/services/N` 404s are gone), the only non-internal links are the map link and the booking phone
    (`tel:`), with no e-mail and no booking-system link left, one `h1` per page, mobile menu opens/closes and closes on
    navigation and on Escape, no horizontal overflow at 375, 768 and 1440 px, first load about 345 KB transferred (the home page
    HTML is 36 KB gzipped, about 21 KB of it the inline track map).
  * **Not verified**: frame rate and smoothness on real devices (the embedded browser reported itself hidden, which throttles
    animation, so no honest number exists), Safari/Firefox rendering, screen-reader behaviour, and colour contrast beyond the
    token pairs that were computed.
  * **Content now comes from the owner** (`frontend/src/content/site.ts` and `backend/knowledge/*.txt`, told to the developer in the
    chat on 2026-09-21 and typed in by hand, so a slip in transcription is possible): booking phone `09177334894`, opening hours
    (Saturday-Wednesday 15:00-24:00; Thursday, Friday and holidays 15:00-01:00), booking only by phone and only for the next day
    (none for the same day, none for Thursday/Friday), 6 single-seaters + 1 two-seater and 8 people per session, and the age /
    height / licence / weight rules. The placeholder phone, e-mail, "Tehran" address, "minimum age 12", "no licence needed" and
    clothing answers were **removed**. The site therefore has no e-mail and no street address, only a map link built from the
    coordinates the owner gave (which point near Shiraz, not Tehran). The «رزرو نوبت» buttons became phone links.
  * **Not confirmed by the owner, or ambiguous**: the prices' unit (the assistant reads 790 / 940 as thousand tomans and «1 تومن» as
    one million; prices are answered by the assistant only, the site shows none), clothing, the street address (`contact-details.txt`
    and `clothing.txt` stay `draft`), whether Thursday/Friday are walk-in days (the owner said "no reservations" on those days while
    the venue is open), and the under-15 riding window, which the owner first wrote as 16-20, then edited on disk to 15-20, and
    finally corrected to **15-18** (Saturday to Wednesday); knowledge files and site FAQ now say 15-18. Also decided by the assistant, not stated by the owner:
    the number 11 in "a child under 11 never drives" (the owner said "for example 11, or whatever you think"), exactly-15-year-olds
    (the owner only said "under 15" and "over 15", so the assistant and the FAQ send them to the venue), and whether the under-15
    day/hour window also applies to a child riding in the rear seat of the two-seater (the owner said nothing, so the rear-seat text
    names no day or hour). The customer-club section is a teaser marked «به‌زودی» (no sign-up or points UI exists), and the
    assistant says so.
  * **The track map is traced from the owner's satellite image** (29.76912 N, 52.49991 E, an 821 x 583 px screenshot, north up).
    The centre line and the lane width at 176 waypoints were snapped onto the white edge lines of the asphalt; the rendered map was
    laid over the photo and the lane edges coincide to about 1-3 px (a 0.3 px average error from compressing the trace to
    waypoints). Two stretches were set by hand because the image has no usable line there: the semicircular hairpin (measured
    from its outer edge and island) and the lane beside the stands.
    At draw time the traced line is smoothed (`smoothTrack` in `frontend/src/lib/track-geometry.ts`; the owner wanted straight
    lanes and even bends): bends are lightly filtered and near-straight stretches are laid on ruler-straight lines, so the
    drawn line can differ from the raw trace by a few px (a straight is split in two rather than allowed to stray more than
    5 units). Not measured against the photo again after smoothing; it was checked by eye only.
    The pit side follows the photo: a paved plaza with the entrance at the top, then a strip of scrub (drawn as green space)
    between the racing lane and the stands, with the lane's own white edge line; the earlier fake pit-lane line was removed.
    The strip's outline is approximate.
    **Not from the image:** the satellite picture is old, so the whole track is lined on both sides with yellow and red tyres
    (except across the open paved apron) as the owner described and the ground photos show, the asphalt is drawn in its current dark colour, the start/finish line position is a
    guess on the straight beside the stands, and the scenery (road, stands, terrace, planter, scrub, fences, pit boxes) is a
    simplified redraw. Nothing is surveyed: do not read dimensions off it. To update it, replace `TRACK_POINTS`/`TRACK_WIDTHS`
    in `frontend/src/content/track.ts` (the tracing scripts were throwaway and are not in the repository).
  * **Deliberately absent**: a contact form (there is no ticket endpoint, and a form that does nothing is worse than none) and
    scroll-reveal animations (CSS scroll-driven animations stalled rendering in the embedded browser; removed twice now).
  * `NEXT_PUBLIC_BOOKING_URL` and `NEXT_PUBLIC_SITE_URL` (fed from `BOOKING_BASE_URL` and `PUBLIC_BASE_URL` by compose) are
    frozen into the web app at build time: after changing either, rebuild the frontend image. Fonts (Vazirmatn, Unbounded) are downloaded from Google during `next build` and self-hosted afterwards, so the
    image build needs network access. `frontend/AGENTS.md` warns that this Next.js version has breaking changes; read
    `node_modules/next/dist/docs/` before writing frontend code.
* **Admin authentication** (Argon2id, TOTP MFA, roles/permissions), audit log, admin dashboards/reports/exports.
* **CMS and media** (typed blocks, drafts, previews, scheduling, versions, media library, `ObjectStoragePort`), **SEO** (metadata,
  sitemap, JSON-LD, redirects), contact form/tickets.
* **Customer club** beyond the ledger/tiers/pricing engine: permanent-discount and coupon storage, birthday and referral
  programmes, campaigns, notes, consent management, profile editing and secure mobile change, deletion/anonymisation requests.
* **Notifications**: real SMS provider adapter, templates, delivery tracking, consent enforcement, in-site notifications
  (`NotificationPort`).
* **Booking**: `BookingGatewayPort` (inquiry + reconciliation polling), OIDC PKCE identity handoff, redirect allow-list.
* **Observability**: Prometheus metrics, OpenTelemetry, Grafana dashboards, the `monitoring` compose profile, load-test scripts and
  results.
* Idempotency-Key support, cursor pagination helpers, CSV/Excel export jobs, GDPR-style retention jobs other than assistant purge.

## Implemented but not verified externally

* **Zarinpal**: adapter follows the documented contract; no merchant id, so no live sandbox call was made.
* **MinIO**: compose uses `quay.io/minio/minio:RELEASE.2024-10-13T13-34-11Z` (Docker Hub no longer hosts MinIO images). It starts
  and reports healthy, but nothing in the backend uses object storage yet (`ObjectStoragePort` is not implemented).
* **AI provider**: exercised by the automated tests only through fakes and recorded response shapes. By hand, on 2026-09-21, about
  35 questions went to a real gateway (GapGPT, `gemma-3-27b-it`), and later an 18-question set was run several times. Most answers
  were right, but **the runs varied**: while the wording was being tuned most had one to three riding-eligibility mistakes (a
  child at exactly 140 cm, a late hour, an adult with no driving experience) and the last had none; calls took 1-22 s against a
  12 s timeout (details in
  `docs/AI_ASSISTANT.md`). The persona makes every riding answer end with a request to state age and height when booking by phone,
  but until a rule check that does not depend on the model exists, treat its eligibility answers as advice, not as the rule. That
  is a sample, not an evaluation; there is no regression set, and a persona or knowledge edit needs a fresh manual check.
* **Semantic answer cache**: implemented, measured on the real model (details on the `feature/semantic-cache` branch), then **retired 2026-09-23**. Running the local embedding model in the API process competed for CPU/RAM with everything else and degraded ordinary answers, so it was removed from `main`; the code and its docs live only on that branch.
* **Conversation memory** is short-term and heuristic: the last 3 exchanges for 20 minutes, in Redis, keyed by the widget's
  per-visit id; follow-up detection looks for pointer words, a leading "and" or a message made only of details, and can miss.
* **Assistant behaviour that is by design but easy to forget**: (conversation memory: see the previous bullet); while the
  published knowledge fits in 12 entries / 8000 characters it is sent whole with each question, so a message costs about 1-5k tokens
  and the model is also called for off-topic messages (its `NO_ANSWER` is discarded by the guard); questions in other languages work
  only if the model can map them onto the Persian text (English worked in the sample); the sync runs at API start-up on one replica;
  the worker and scheduler containers run the image they were last created with, which is irrelevant to the assistant.
* **CI workflow**: written, never run on a runner. Only its YAML was parsed, and its `pip-audit` step was reproduced locally in a
  `python:3.12-slim` container against `backend/requirements.lock` (no known vulnerabilities at that time).
* **Nginx** was started via compose and exercised locally (health through the proxy, frontend page, JSON error envelope,
  `/api/v1/health/ready`, `/api/docs` and `/api/openapi.json` answering 404 by design). The edge limits were measured: the OTP
  zone accepted 6 of 12 rapid requests (1 + burst 5), the API zone 41 of 150 (1 + burst 40), a 2 MB body got 413. Behaviour under
  sustained load and behind a real client-IP-forwarding edge (the limits key on `$binary_remote_addr`) were not tested.

## Known design limits

* Sample loyalty tiers (Regular/Silver/Gold/VIP with 0/1000/5000/10000 points) exist only so the ledger can be demonstrated;
  they are placeholders, not business rules.
* `handle_event` (Celery) logs receipt only: no event consumers are registered yet, so `UserRegistered`, `PaymentSucceeded`,
  `BookingVerified` etc. accumulate as published outbox events.
* Circuit breaker state is per process by design (each replica protects itself).
* Fixed-window rate limiting allows short bursts at window boundaries.
* Log masking is a last line of defence, not a guarantee: it recognises unseparated Iranian mobile numbers (`09…`, `+98…`,
  `0098…`), bearer tokens and `otp|code|password|api_key|authorization|token|secret|authority` `key=value` pairs. Numbers formatted
  with spaces or dashes, free-text secrets and values inside dict/JSON reprs (`{'code': '123456'}`) are not recognised, so
  application code must still avoid logging them (the last gap is also why the development-only OTP echo stays readable; the
  phone number next to it is masked). It applies to
  the API (including uvicorn's access log), the Celery worker and beat. nginx does not mask; its access log records the request
  path only (never the query string) plus a `rid` equal to the API's `request_id`.
* **No TLS in the stack**: nginx listens on plain HTTP `:8080`. Production needs a TLS-terminating edge (or certificates added to
  nginx). The frontend's HTML, served through the proxy, gets only `X-Content-Type-Options`, `X-Frame-Options` and
  `Referrer-Policy`: **no Content-Security-Policy and no HSTS**, to be designed together with the real frontend. The API sets
  its own `default-src 'none'` CSP on JSON responses (docs pages exempt) and HSTS when `APP_ENV=production`.
* The backend image build fetches its build backend (`setuptools>=75`, unpinned) from PyPI at build time, so it needs network
  access and is not fully reproducible even though runtime dependencies are locked.
* Points reversal of already-spent earned points can drive a balance negative (it is auditable and blocks further spending);
  the business policy for this is undecided.

## Housekeeping

The previous scaffold's `backend/app` and root `nginx.conf` were deleted on 2026-09-21 with the owner's approval (nothing referenced
them; the live proxy config is `nginx/nginx.conf`). Identical copies of the whole old scaffold remain in `_legacy/` and can be
removed whenever nobody needs them. `backend/tests` is the current test suite; the old tests are only in `_legacy/tests`.
