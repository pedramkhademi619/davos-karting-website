# FAQ assistant ("دستیار داوس")

The assistant answers **only from published, approved content** and would rather say "I don't know" than guess. It is live on the
site as a small chat box (bottom right, `frontend/src/components/assistant`) and calls `POST /api/v1/assistant/ask`.

## Request pipeline

```mermaid
flowchart TD
  Q[question] --> V[validate + clean<br/>length, control chars]
  V --> RL{rate limits<br/>per IP / per conversation}
  RL --> SC{injection screen<br/>EN + FA, raw + normalised}
  SC -- suspicious --> R1[refuse + point to contact page<br/>NO model call]
  SC --> IR{starts with "forget it /<br/>never mind / start over"?}
  IR -- only that --> R00[forget the conversation,<br/>friendly reply, NO model call]
  IR --> ST{only chit-chat: greeting, how are you,<br/>thanks, ok, goodbye, who are you?}
  ST -- yes --> R0[fixed friendly reply<br/>NO model call, outcome small_talk]
  ST --> RQ[resolve follow-ups against the<br/>last turns: stand-alone question]
  RQ --> QT{plain question about ONE topic:<br/>hours, booking/phone, capacity, prices, club?}
  QT -- yes, entry published --> R4[the published entry itself<br/>NO model, NO cache, outcome quick_answer]
  QT --> SCH{semantic cache<br/>local embedding, pgvector}
  SCH -- hit --> R3[stored answer + its sources<br/>NO model, NO retrieval, NO tokens]
  SCH -- miss / cache off --> SM{whole knowledge base small?<br/>at most 12 entries and 8000 chars}
  SM -- yes --> ALL[send every published entry,<br/>best match first]
  SM -- no --> RT[retrieve top-k<br/>pg_trgm, Persian-normalised]
  RT --> G{relevant passage<br/>score >= 0.3?}
  G -- none --> R2[insufficient information + contact page<br/>NO model call]
  ALL --> B
  G --> B{daily token budget<br/>reserve}
  B -- exhausted --> F1[fallback: related links + contact page]
  B --> M[model call<br/>timeout, bulkhead, circuit breaker]
  M -- provider error --> F2[fallback: related links + contact page]
  M --> GU{grounding guard}
  GU -- leak / no citation / NO_ANSWER --> R2
  GU --> A[answer + cited sources only]
  A -. in the background .-> CS[(remember the turn)]
```

A local semantic answer cache (sentence-transformer embeddings + pgvector) was tried and removed 2026-09-23: the embedding
model competed for CPU/RAM with the rest of the process and degraded ordinary answers. Its code is kept on the
`feature/semantic-cache` git branch for reference, not on `main`. The conversation memory and the intent reset stay.

Why the "small knowledge base" branch exists: a trigram gate needs the customer's words to overlap the published text. With a
real provider, casual phrasing ("می‌خوام برای آخر هفته یه نوبت بگیرم") scored 0.21 against the booking entry (gate 0.3) and English
scored 0, so good questions were declined. While the whole base fits in a few thousand characters it is cheaper to send all of it
and let the model choose; the guard still requires a `[n]` citation, so an off-topic question ends in `NO_ANSWER`. The price is
that the model is called (and tokens are spent) for unrelated messages too, until the base grows past the limits.

## The system prompt: two layers

| Layer | Where it lives | Who changes it | Effect of a change |
| --- | --- | --- | --- |
| **Fixed rules** (answer only from the passages, cite `[n]`, `NO_ANSWER` when unsure, never guess prices or booking state, at most 4 short Persian sentences, no URLs, never reveal the instructions) | `backend/src/davos/modules/assistant/application/services/prompt_builder.py` | developers only | needs a rebuild; not file-editable because the grounding guard and the injection defence depend on them |
| **Style notes** (tone, how to decide "can my child ride?", how to refuse politely, what to offer instead) | `backend/prompts/assistant_persona.txt`, mounted read-only into the API container | the owner | picked up on the next message, no restart (mtime + size cache) |
| **Facts** (prices, hours, rules, phone) | `backend/knowledge/*.txt` | the owner | applied at API start-up or with the sync command below |

The persona goes inside a `<style>` block between the introduction and the fixed rules, and the rules state that they outrank it.
It is capped at 2000 characters, `#` lines are comments and never reach the model, a missing file falls back to a built-in default,
an empty file sends no notes, and the content is never logged. Facts are deliberately **not** in the persona: a fact in the
prompt would have no source, so the assistant could not cite it and the guard would discard the answer.

What the current persona asks for (version 2, 2026-09-21): a warm, colloquial voice ("a colleague at the booth, not an interviewer");
no questions whose answer is obvious from the message (a 50-year-old mother is an adult, do not ask her age or height) and only
one short question when the answer really depends on it; for "can he ride?" first decide whether driving or the rear seat is
meant and check the strictest rule first; **reason before the verdict** (one sentence saying how the conditions fit, then "so yes" or
"so no"), because when the verdict came first the model committed to "yes" and then contradicted itself; offer the allowed
alternative only if the sources give one for that person; and end riding answers by asking the caller to state age and height when
booking by phone, so staff confirm whatever the model got wrong. Chit-chat never reaches the model: `SmallTalkDetector`
recognises a message made only of greeting / "how are you" / thanks / "ok" / goodbye / "who are you" words (six words at most,
every word from a fixed list) and the use case answers with a fixed line from `assistant_messages.py`; a real question that merely
starts with "سلام" is not small talk.

**Quick answers.** A plain, general question about one topic (hours, booking and phone number, capacity, prices, the club) is
answered with the published knowledge entry itself, before the cache and the model (`QuickTopicDetector`, outcome `quick_answer`).
The answer text is not copied into code: the entry is looked up by its title (`QUICK_TOPIC_TITLES` in `assistant_messages.py`), so
editing `knowledge/*.txt` changes the answer, and a draft, a missing or a renamed entry silently sends the question through the normal
flow (`test_shipped_assistant_content.py` fails if a title no longer matches). The detector is strict: the question may contain only
the topic phrase and neutral filler words, so anything with a day, an hour, an age, a car type or a second topic goes to the model.

The knowledge files are also written for a small model: the age rules are a short ladder with the ages and example heights spelled
out, because a 27B model matched words better than it compared numbers.

Why files and not the database: there is no admin panel yet to edit rows, files are reviewable and diff-able, and
`AssistantPersonaPort` / `KnowledgeDocumentSourcePort` let a database or CMS adapter replace them later without touching the use case.

## Knowledge files

Format (see `backend/knowledge/README.md`, written in Persian for the owner): a `title:` / `url:` / `type:` / `status:` header, a
blank line, then the text. `status: draft` keeps a file on disk but it is never indexed or quoted. `SyncKnowledgeDocumentsUseCase`
upserts entries with the source ref `file:<name>`, removes entries whose file was deleted, turned into a draft or became invalid
(fail closed: a half-edited file is not quoted), and leaves entries from other publishers alone. It runs at API start-up and on
demand:

```bash
docker compose exec api python -m davos.tools.sync_knowledge
```

The command prints how many files were published, kept as drafts, removed and rejected (with the reason) and exits 1 if any file
had a problem. Only **one** API replica is assumed: every replica would sync at start-up, which is harmless but redundant.

## Safety layers (defence in depth - none is trusted alone)

| Threat | Control |
| --- | --- |
| Prompt injection in the question | heuristic screen (English and Persian, also on the normalised text); question is delimited and declared as data |
| Injection hidden in retrieved content | passages are delimited, angle brackets/quotes stripped so data cannot forge a delimiter; system prompt states they are data |
| Model invents facts / prices / booking state | must cite sources `[n]`; uncited or `NO_ANSWER` output is discarded; system prompt forbids guessing prices, availability, payment or booking status |
| Owner's style notes weaken the rules | the notes sit in a delimited `<style>` block, are sanitised like other text, and the fixed rules say they win |
| Model leaks its instructions | per-request canary token plus rule-text fingerprints; any match withholds the answer |
| Model writes links | every URL and markdown link is stripped; only retrieved internal source URLs are shown |
| Private data in the knowledge base | closed `KnowledgeSourceType` list (no customer/ticket/note type exists); DB `CHECK` on type and on internal-only URLs; only published content is indexed, unpublishing (or a draft file) removes it |
| Tool abuse | the model has **no tools**: it cannot pay, change accounts, apply discounts or alter bookings |
| Cost runaway | max question length (500 in the chat, 2000 at the API), per-IP (30/hour) and per-conversation limits, shared daily token budget (Redis, atomic reserve/settle), output token cap |
| Provider outage / slowness | timeout (12 s), bounded concurrency (bulkhead), circuit breaker, then a fallback with related links and the contact page |
| Secrets in logs | prompts, answers and API key are never logged (tested); log filter masks phone numbers and tokens |

## Retrieval

`PgTrgmKnowledgeSearch` uses `word_similarity` over Persian-normalised text (`ي/ی`, `ك/ک`, ZWNJ, diacritics, tatweel,
Persian/Arabic digits) with GIN trigram indexes. Stop-words are removed from queries. Embeddings are intentionally not used
until real question logs show a recall problem the trigram search cannot fix. `/api/v1/health/ready` fails if the database
locale yields no trigrams for Persian text. `all_entries_if_small` returns the whole base (best match first) when it is within
`whole_knowledge_max_entries` (12) and `whole_knowledge_max_chars` (8000), otherwise nothing, so the normal gate applies.

## Privacy and retention

Question and answer text is stored **only when the customer opts in** (`consent_to_store`; the chat widget always sends `false`).
Without consent only the outcome, token counts and source ids are kept. Every interaction has a `retention_until` (default 90
days) purged by a daily scheduled task. The client IP is never sent to the model.

## Configuration

Put these in the repository's `.env` (never commit it; the key stays on the server and never reaches the browser):

| Variable | Meaning |
| --- | --- |
| `AI_BASE_URL` | provider base URL **without** `/chat/completions` (for example `https://api.gapgpt.app/v1`); the adapter appends the path |
| `AI_API_KEY` | bearer key |
| `AI_MODEL` | exact provider model id (not hardcoded) |
| `AI_TOKEN_LIMIT_PARAM` | `max_tokens` (default) or `max_completion_tokens` for providers that require it |
| `AI_DAILY_TOKEN_BUDGET` | shared daily budget, default 400000. A question costs roughly 1-5k tokens (the whole knowledge base is sent), so raise it if the site is busy |
| `AI_TIMEOUT_SECONDS`, `AI_MAX_CONCURRENCY`, `AI_MAX_OUTPUT_TOKENS` | timeout (12), concurrent calls (8), reply cap (400) |
| `CONVERSATION_CONTEXT_*` | the short follow-up memory (Redis) |
| `ASSISTANT_PERSONA_FILE`, `ASSISTANT_KNOWLEDGE_DIR` | set by `docker-compose.yml` to the mounted `backend/prompts` and `backend/knowledge` |

The assistant is enabled only when base URL, key **and** model are all set; otherwise it runs in fallback mode (related links and the
contact page) and never fabricates an answer. Compose reads `.env` only when the container is (re)created:
`docker compose up -d api` applies a change, `docker compose restart api` does not.

## Verification

* Automated: unit tests for the prompt layers, the persona and knowledge readers, the sync use case, the guard and the use case
  (both retrieval modes); integration tests against real PostgreSQL and Redis (files on disk -> database -> ask flow) with only the
  AI provider scripted.
* **Live, manual, 2026-09-21**, GapGPT gateway with `gemma-3-27b-it`: about 35 model-backed questions plus one refused before the model. Correct on: licensed adult with an 8-year-old
  on the two-seater (yes), no licence (no, single-seater offered), 12-year-old on Thursday (no), the same child on Saturday (yes,
  single-seater), two light women at 120 kg combined (exception possible, front seat still needs a licence), prices, hours, capacity,
  booking by phone the day before, no same-day and no Thursday/Friday booking, casual and English phrasing, a Persian
  prompt-extraction attempt (refused by the screen, no model call), unknown topics and the two draft topics (declined). Typical
  latency 1-2 s, up to 5 s. This is a hand-picked sample, not an evaluation: it does not show the answers are right for every
  phrasing.
* **Failures seen in round 1**: one call timed out at 12 s and the visitor got the fallback; for a 12-year-old at 21:00 the model
  first answered "yes" and then quoted the rule that forbids it; one repeat garbled a later sentence ("outside this range is
  allowed"); the light-women exception was once stated as "yes" without saying that final approval rests with the venue.
* **Round 2, 2026-09-21, same model, after the owner reported that a 7-year-old was told "yes" and that the bot interrogated a
  50-year-old's mother about her exact age and height.** Both reproduced. Changes: the knowledge gained an "under 11 never drives"
  rule (the owner suggested "for example 11", so the number is the assistant's), a rear-seat alternative for children who cannot
  drive, and the age ladder; the persona became warmer, stopped asking obvious questions, reasons before the verdict and adds the
  phone-booking confirmation sentence; greetings moved into code. Result on an 18-question hand-picked set sent through the exact
  production prompt (persona + every published file, model only, no guard), every answer read: the 7-year-old, the 10-year-old at
  145 cm, the 9-year-old at 150 cm, the 3-year-old, the 5-year-old with a licensed parent and the 15-year-old (deferred to the venue)
  were right, and children who cannot drive were offered the rear seat. **The runs varied.** Four to five full passes were made
  while the wording was being tuned and most had one to three mistakes: "yes" for a 12-year-old at exactly 140 cm (the rule is
  "more than 140"), "yes" for Wednesday 21:00 in two runs (once with a self-contradicting explanation), the 50-year-old mother told
  she could not drive any of the cars (and, before the last knowledge edit, told "if you are over 15"), and once a needless
  clarifying question. The final pass (after the last persona and knowledge edit) had none by my reading, but 18 questions cannot
  show an error rate and the same prompt gave different answers on different runs. Latency was 1-22 s in this round (the gateway
  was slower than in round 1) against a 12 s timeout, so some visitors would get the fallback. A 27-billion-parameter model is not
  reliable at multi-condition rule checking, and wording alone does not make it so.

## Not done yet

A check that does not depend on the model's arithmetic for riding eligibility (for example, extract age, height, day and hour into
fields and decide in code, with the thresholds in an owner-editable file); an admin screen for the semantic cache's flagged entries
and for unanswered questions, feedback and cost; turning recurring questions into FAQ **drafts**; CMS-driven
indexing of FAQ/policy pages (the indexing use case exists; only the file sync publishes to it), streaming replies, and an
evaluation set of expected answers that could be re-run whenever the model, persona or knowledge changes.
