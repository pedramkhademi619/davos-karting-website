# Semantic answer cache and conversation memory

A customer who asks what somebody asked before gets the stored answer at once: no model call, no retrieval, no tokens.
Only a question the cache cannot answer goes to the language model, and its grounded answer is stored for the next customer.

**Everything runs on this machine.** The embedding model is a folder of files read from disk, the vectors live in the compose
PostgreSQL (`pgvector`), the short conversation memory lives in Redis. No embedding service, no hosted API and no sidecar
container is involved, and at run time the API is started with `HF_HUB_OFFLINE=1`, so even an accidental download fails. The
only remote call left in the assistant is the language model on a cache miss, to the provider configured in `.env`
(`AI_BASE_URL`); that is the model's job, not the cache's. The one thing fetched from the internet is the model *files*, once
and on purpose (see [Setup](#setup-once)).

## Where it sits

See the pipeline in [AI_ASSISTANT.md](AI_ASSISTANT.md). After the safety screens and the greeting shortcut, a question is
turned into a stand-alone question (follow-ups), embedded on the CPU, and the nearest stored questions are fetched from
PostgreSQL. An entry may answer only if every rule below holds. A miss follows the normal grounded flow, and a grounded answer
is stored *after* the response has gone out (`AsyncioBackgroundRunner`), so it never adds to the customer's wait.

## Why a plain semantic cache would be unsafe here

Sentence embeddings measure topic, not detail. "Opening hours on Thursday" and "opening hours on Saturday", "a 12-year-old of
140 cm" and "of 135 cm", "single-seater" and "two-seater", "can I book" and "can't I book" are near-identical to the model and
have different answers. Karting is exactly the domain where the detail is the answer (age, height, weekday, holiday prices, who
may sit in which kart). A cache that serves the first customer's answer to the second would eventually tell a parent that a child
may drive when the rule says otherwise, and would repeat it to everybody. So similarity alone never decides.

## The rules that make a hit legitimate

| Rule | Why | Implemented in |
| --- | --- | --- |
| cosine similarity at least `SEMANTIC_CACHE_SIMILARITY_THRESHOLD` (default **0.94**, measured: see below) | the wording is the same question | `PgVectorSemanticCache` (HNSW, `<=>`), `CacheHitSelector` |
| **same signature**: the same numbers and the same discriminator words (weekdays, regular/holiday, single/two-seater, child/adult, negations, ages and units, licence, weight, height) | the details that decide an answer must be identical | `QuerySignatureBuilder`, `discriminator_lexicon.py`; more words via `SEMANTIC_CACHE_EXTRA_DISCRIMINATORS` |
| **same fingerprint**: a hash of the published knowledge, the style notes, the fixed prompt rules, the model id and the cache schema version | an answer is only valid for the inputs that produced it; when the owner edits a price or the persona, every older entry stops matching at once | `AnswerFingerprint`, `PgKnowledgeDigest`, `PromptBuilder.rules_version()` |
| made by the same embedding model | vectors of different models are not comparable | `embedding_model` column |
| active and not flagged | a person or a customer's "not helpful" retired it | `is_active`, `is_flagged_for_review` |
| not older than `SEMANTIC_CACHE_MAX_AGE_DAYS` (30) | even a correct answer should be re-earned now and then | `find_candidates(not_before=...)` |

What is **never** stored: an answer that cites a `policy` source (the rules about who may drive or sit where; a wrong "yes" would
be repeated to everyone, so those questions always reach the model; configurable with
`SEMANTIC_CACHE_EXCLUDED_SOURCE_TYPES`); anything that is not a grounded model answer (fallbacks, refusals, "I don't know",
greetings); a fragment that only makes sense after an earlier question but arrives without one ("و برای روز تعطیل؟" as the
first message: the model can only guess its subject, and a cached guess would be served to everybody who types the same words;
found and fixed during live testing); questions or follow-ups that contain a phone number, an e-mail address or a long digit
string (they are not even embedded); answers shorter than two characters or without a cited source.

If a customer rates a served answer "not helpful", the entry is flagged for review and deactivated at once
(`SubmitFeedbackUseCase`). The customer whose question *created* an entry can retire it the same way. Failures never reach the
customer: if the model is not loaded yet, PostgreSQL errors, or the write fails, the question simply continues to the language
model as if there were no cache.

## Conversation memory

* **Intent reset** (`IntentResetDetector`, regular expressions, no model): a message that *opens* with "فراموشش کن", "بی‌خیال",
  "ولش کن", "شروع از اول", "never mind", "forget it", "ignore previous context", "start over", "ما هي…" and so on forgets the
  conversation. Alone, it gets a friendly one-line answer without a model call; followed by a real question, the question is
  answered with a clean slate. "start over" *inside* a question ("how do I start over a failed booking") is not a command.
* **Follow-ups** (`FollowUpDetector`, `QueryResolver`): a short message that leans on the previous one ("هزینه‌ش چقدره؟", "و
  پنجشنبه؟", "what about its price?") is joined to the previous stand-alone question before the cache lookup, so the cache never
  stores or matches the bare fragment. A fragment that has nothing to lean on (typed as the first message) is answered by the
  model without touching the cache at all. It is a heuristic (pointer words, a leading "and", or a message made only of
  details); a wrong guess is harmless: it costs a cache miss, never a wrong answer.
* **Memory** (`RedisConversationContext`): the last `CONVERSATION_CONTEXT_TURNS` (3) exchanges of a conversation, forgotten after
  `CONVERSATION_CONTEXT_TTL_SECONDS` (20 minutes) of silence, keyed by the widget's per-visit `conversation_id`. It is working
  memory for understanding a follow-up, never written to the database.
* **History in the prompt**: the model receives the recent turns in a `<history>` block that the fixed rules declare to be data,
  not instructions, and not a source of facts; angle brackets and quotes inside it are neutralised like every other untrusted
  text, and the injection screen refuses messages that try to forge its delimiters.

## Data

`assistant_semantic_cache` (migration `0007`, which also runs `CREATE EXTENSION IF NOT EXISTS vector` first):

| Column | Meaning |
| --- | --- |
| `id`, `created_at`, `last_used_at`, `hit_count` | identity and usage (a hit updates the last two in the background) |
| `original_query`, `resolved_query` | what the customer typed, and the normalised stand-alone text that was embedded |
| `signature`, `fingerprint`, `embedding_model` | the guards above |
| `embedding` `vector(768)` | with an **HNSW** index (`m=16`, `ef_construction=64`, cosine) |
| `response`, `sources` (JSONB), `language` (`fa`/`ar`/`en`) | the answer, the sources shown with it, the detected language |
| `is_active`, `is_flagged_for_review` | review state (see the TODO in `SemanticCacheEntryModel` for the future admin panel) |

`assistant_interactions` gained `cache_entry_id` and `served_from_cache`, so the hit ratio and the tokens saved can be read
straight from the table:

```sql
SELECT count(*) FILTER (WHERE served_from_cache) AS served_from_cache,
       count(*) FILTER (WHERE outcome = 'answered') AS answered,
       round(100.0 * count(*) FILTER (WHERE served_from_cache) / nullif(count(*) FILTER (WHERE outcome = 'answered'), 0), 1) AS hit_percent,
       sum(prompt_tokens + completion_tokens) AS tokens_spent
FROM assistant_interactions WHERE occurred_at > now() - interval '7 days';
```

**Privacy.** The widget never asks to store the conversation, and the interaction log respects that. The cache is a deliberate,
narrow exception: it keeps the *text of the question* (anonymous: no user id, IP address or conversation id) so that it can be
compared with later questions, after the checks above have kept out phone numbers, e-mail addresses and long digit strings. A
question like "my mother is 50" can still be stored. If that is not acceptable, set `SEMANTIC_CACHE_ENABLED=false`; the assistant
then works exactly as before and nothing is written. Tell the site's privacy note about this before enabling it publicly.

## Setup (once)

```bash
docker compose build api postgres migrate          # the api image carries CPU-only PyTorch and sentence-transformers
docker compose --profile tools run --rm fetch-embedding-model   # the only step that uses the internet: ~1.1 GB, once
docker compose up -d                                # postgres now has pgvector; migrate creates the table
docker compose exec api python -m davos.tools.calibrate_semantic_cache
```

The model (`intfloat/multilingual-e5-base`, 278 M parameters, Persian, Arabic and English, 768 dimensions) is downloaded at a
pinned commit as plain files (about 1.1 GB) into `backend/models/`, which is git-ignored and mounted read-only. From then on
nothing needs the internet. On a machine that must stay offline, copy that folder from another machine. Without the folder the
API logs how to fetch it and the cache stays off.

Check it: the API log shows `embedding model ready`; ask the same question twice in the chat and the second answer comes back
in milliseconds (`from_cache: true` in the JSON); `docker compose exec api python -m davos.tools.calibrate_semantic_cache` prints
the similarity of paraphrases, contrast pairs and unrelated pairs and fails if any of the last two would be served.

Day to day:

* **Purge** now: `docker compose exec api python -m davos.tools.purge_semantic_cache` (the scheduler runs it daily). It removes
  entries not used for 90 days and entries made under other knowledge, style notes, rules or model that have not been served for
  a week; entries flagged for review stay. A process that works out a different fingerprint (say a worker with another persona
  file) can only remove entries nobody has been served for a week, never live ones.
* **Turn off**: `SEMANTIC_CACHE_ENABLED=false` in `.env`, then `docker compose up -d api`. **Stricter**: raise
  `SEMANTIC_CACHE_SIMILARITY_THRESHOLD`. **New contrast word** (a new vehicle, a new kind of day): add it to
  `SEMANTIC_CACHE_EXTRA_DISCRIMINATORS` (a JSON list) and re-run the calibration tool.
* **Another model**: the column is `vector(768)`; a model with another size needs a new migration. Entries of other models are
  ignored automatically.

## Settings

| Variable | Default | |
| --- | --- | --- |
| `SEMANTIC_CACHE_ENABLED` | `false` in code, `true` in compose | master switch |
| `SEMANTIC_CACHE_SIMILARITY_THRESHOLD` | `0.94` | 0.5 to 1.0; see "Measured" before lowering it |
| `SEMANTIC_CACHE_CANDIDATES` | `8` | nearest entries fetched, then filtered by signature |
| `SEMANTIC_CACHE_MAX_AGE_DAYS` | `30` | |
| `SEMANTIC_CACHE_EXCLUDED_SOURCE_TYPES` | `["policy"]` | never cache answers citing these kinds of source |
| `SEMANTIC_CACHE_EXTRA_DISCRIMINATORS` | `[]` | extra words that must match exactly |
| `EMBEDDING_MODEL_PATH` | compose: `/models/multilingual-e5-base` | folder with the model files |
| `EMBEDDING_MODEL_NAME`, `EMBEDDING_DIMENSION` | `intfloat/multilingual-e5-base`, `768` | identity stored with entries, and a check at load |
| `EMBEDDING_THREADS`, `EMBEDDING_LRU_SIZE` | `2`, `1024` | CPU threads for inference; recent texts remembered |
| `CONVERSATION_CONTEXT_TURNS`, `CONVERSATION_CONTEXT_TTL_SECONDS` | `3`, `1200` | conversation memory |

## Measured

Everything below was measured on this machine with the real model (`intfloat/multilingual-e5-base`, CPU, 2 threads, inside the
API container with its 2 GB limit). Re-run it with `docker compose exec api python -m davos.tools.calibrate_semantic_cache`.

**Cost.** The model loads in about 8-9 s (in the background, the API is ready at once) and the API process uses about 750-850 MB.
Embedding one question takes about 60 ms (median; 95th percentile about 100 ms). The API image is 2.1 GB (the light image of the
worker and scheduler is 360 MB); the model files are 1.1 GB on disk.

**Why 0.94.** E5 similarities are compressed: everything about the same business scores high, so a threshold that sounds strict
is not. Ten topics of the site (booking, hours, prices, capacity, club, address, clothing, two-seater rules, single-seater rules,
support) were each asked three ways, and every pair was scored: 30 same-topic pairs and 405 cross-topic pairs. A pair counts as
served when its similarity reaches the threshold *and* its signatures match.

| threshold | different-topic pairs wrongly served (of 405) | contrast and unrelated pairs wrongly served (of 15) | everyday rewordings served (of 12) | same-topic pairs in other words served (of 30) |
| --- | --- | --- | --- | --- |
| 0.86 | 38 | 1 | 12 | 18 |
| **0.88 (the brief)** | **15** | **1** | 12 | 13 |
| 0.90 | 6 | 0 | 12 | 10 |
| 0.92 | 1 | 0 | 12 | 4 |
| **0.94 (the default)** | **0** | **0** | **11** | 1 |
| 0.96 | 0 | 0 | 8 | 0 |

The cross-topic pair that slips through at 0.88-0.92 is not a silly one: "how do I book a slot?" and "what is the capacity of a
slot?" score 0.927 and "how do I book?" and "where is the track?" score 0.898. At the brief's 0.88 a customer could have been
given the capacity answer to a booking question. The contrast pairs (another weekday, 140 vs 135 cm, 10 vs 16 years, regular vs
holiday, single vs two-seater, "can" vs "cannot", licence vs no licence) all score **0.954-0.990**, above 0.88 on similarity
alone (9 of 9 would have been served wrongly), and the signature guard blocks every one of them.

**What that means.** The cache reliably serves the same question worded slightly differently (a different ending, an extra
"شما", a greeting in front, English capitalisation: 11 of 12 at 0.94, the miss is «چنده» vs «چند است» at 0.936). It does *not*
try to match genuine paraphrases in other words (3 of 11 at 0.94); those go to the model, which is the safe side. Repeat traffic
to an FAQ assistant is mostly the first kind. The measurement uses about 100 hand-written questions; the more real questions you
add to `calibrate_semantic_cache.py`, the better the threshold is justified.

**Live, through the running API** (the model being your configured one): a repeated question came back in 23 ms instead of
2.7 s; "سلام ساعت کاری شما چیه؟" and "ساعت کاری چیه؟" were answered from the entry made for "ساعت کاری شما چیه؟" in 81 ms and
66 ms (the model takes 1.7-13 s); Thursday and Saturday opening hours both went to the model; the question about a 7-year-old
(a policy) went to the model twice; "فراموشش کن" was answered in 10 ms without the model; a "not helpful" rating returned 204 and
the next identical question went to the model again.

## Decisions that differ from the original brief

The brief was written for a fresh FastAPI project (`core/`, `models/`, `schemas/`, `services/`, `api/v1/`). Where a different
decision was better for this codebase, the decision below was taken:

1. **It lives inside the assistant module**, not in a parallel flat layout. Ports (`EmbeddingPort`, `SemanticCachePort`,
   `ConversationContextPort`, `KnowledgeDigestPort`, `BackgroundRunnerPort`), pure domain rules and adapters follow the layer
   contracts the repository enforces (one class per file, import-linter, strict mypy). The "singleton embedding" is the
   container's single `SentenceTransformerEmbedding`; the "session manager" is `ConversationContextPort` (Redis, with an in-memory
   twin for tests); `services/` split across `domain/services` and `application/services`.
2. **The model runs in the API process** (loaded in a background thread at start-up, inference on one dedicated worker thread,
   a small LRU for repeated texts), because you asked for everything local with no API in between. Until it is loaded, questions
   skip the cache instead of waiting. The API container got 2 GB of memory (the model alone needs about 1.2 GB) and 2 CPUs; the
   worker, scheduler and migration job keep the small image.
3. **Similarity is not enough**, hence the signature, the policy exclusion, the fingerprint, the age limit and the feedback
   retirement above. None of them is in the brief; each closes a way for a cache to repeat a wrong or outdated answer.
4. **More columns**: `signature`, `fingerprint`, `embedding_model`, `sources` (a cached answer must keep its citations, which the
   widget shows), plus `cache_entry_id` and `served_from_cache` on interactions.
5. **Follow-up resolution is a heuristic**, not a second model call: a reformulation call would cost the latency and tokens the
   cache exists to save, and the previous question is a good enough subject for the lookup key.
6. **No streaming.** The grounding guard must see the whole answer (citations, prompt-leak canary, links) before anything is
   shown, and a cached answer is instant anyway.
7. **pgvector is compiled into the existing Alpine Postgres image** (`postgres/Dockerfile`, source pinned by SHA-256) instead of
   swapping to the Debian `pgvector` image, which would change libc and text collation under the existing data volume. Filtered
   nearest-neighbour queries set `hnsw.iterative_scan` so stale or inactive entries closer than the real match cannot hide it
   (a test proves the query returns nothing without it).
8. **The default threshold is 0.94, not the brief's 0.88.** On the real model 0.88 wrongly served 15 of 405 pairs of different
   topics (see "Measured"). It stays configurable, and a tool re-checks any value against your own questions.

## Limitations

* The guard is a vocabulary, not understanding. A contrast that is not in `discriminator_lexicon.py` (a new vehicle, an unusual
  qualifier) is not caught by the signature; the threshold, the policy exclusion, the age limit and the feedback retirement are
  the remaining defences. Add new contrast words as the business grows and re-run the calibration tool.
* Two customers asking the same new question at the same moment both reach the model and both store an answer (harmless
  duplicates, the most similar one wins).
* There is no admin screen yet for reviewing flagged entries (the columns and a `TODO` are in place); until then use SQL.
* The cache stores question text without consent (see Privacy) and a stored answer can be up to 30 days old.
