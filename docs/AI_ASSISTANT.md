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
  RQ --> LS[(live booking settings<br/>admin panel, 30 s cache)]
  LS --> QT{plain question about ONE topic:<br/>hours, booking/phone, capacity, prices, club?}
  QT -- yes --> R4[published entry, or the live settings<br/>for prices and capacity<br/>NO model, outcome quick_answer]
  QT --> SM{whole knowledge base small?<br/>at most 12 entries and 8000 chars}
  SM -- yes --> ALL[send every published entry,<br/>best match first]
  SM -- no --> RT[retrieve top-k<br/>pg_trgm, Persian-normalised]
  RT --> G{relevant passage<br/>score >= 0.3?}
  ALL --> CK
  G -- none, and no rule check --> R2[insufficient information + contact page<br/>NO model call]
  G --> CK[add computed passages last:<br/>live settings + rule checks for<br/>ages, height, day, hour, weights, group]
  CK --> B{daily token budget<br/>reserve}
  B -- exhausted --> F1[fallback: related links + contact page]
  B --> M[model call: main model, backup model on failure<br/>timeout, bulkhead, circuit breaker per model]
  M -- both fail --> F2[fallback: related links + contact page]
  M --> GU{grounding guard}
  GU -- no citation / other script --> RP[one repair call:<br/>rewrite with citations, Persian only]
  RP --> GU2{grounding guard}
  GU2 -- still not showable --> R2
  GU -- leak / NO_ANSWER --> R2
  GU --> A[answer + cited stored sources]
  GU2 --> A
  A -. in the background .-> CS[(remember the turn)]
```

A local semantic answer cache (sentence-transformer embeddings + pgvector) was tried and removed 2026-09-23: the embedding
model competed for CPU/RAM with the rest of the process and degraded ordinary answers. Its code is kept on the
`feature/semantic-cache` git branch for reference, not on `main`. The conversation memory and the intent reset stay.

## Rule checks and live settings (numbers are compared by code, not by the model)

Language models are unreliable at "is 140 more than 140", "65 + 65 below 130?", "is 18:30 inside 15 to 18" and at planning
sessions for a group; every model tested made at least one such mistake when it had to work it out from prose. So the numbers are
compared in code and the model only explains the result:

* `PartyFactsExtractor` (domain) reads what the message literally says: ages ("۷ و ۹ ساله", "دوازده سالشه"), height, weekday, hour
  (a bare "ساعت ۵" is 17:00 because the track opens at 15:00), weights, group size ("۹ نفریم", but "دو نفره" is the two-seater),
  licence yes/no. It never guesses; what it cannot read is left out. A follow-up that only adds a detail ("قدش ۱۵۰ـه") is combined
  with the people named in the previous question.
* `EligibilityAdvisor` applies the owner's rules (`EligibilityRules`: under 11 never drives, 11-14 only above 140 cm on Saturday to
  Wednesday 15:00-18:00, exactly 15 is decided by the venue, two-seater front 18+ with a licence, rear seat 4-15, two light women
  strictly below 130 kg together) and writes one plain sentence per person with the verdict first ("نتیجه: نه ...").
  `GroupSessionPlanner` computes the fewest sessions and a seating plan for a group.
* The kart counts, prices, holiday and closed weekdays, hold minutes and whether online booking is open are **not** in code or in the
  knowledge files: they are the admin panel's booking settings, read live through `BookingFactsPort` (composition adapter
  `ScheduleBookingFacts`, cached 30 s). `EligibilityRules.for_booking` applies them to the checks, `BookingFactsPassage` states them
  in Persian. Changing the number of single-seaters in the admin panel changes the assistant's group plans and capacity answers.
* Both results are added as passages marked `checked="true"`, placed last (right before the question, so stored knowledge keeps its
  numbers), and fixed rule 5 tells the model they are decisive and must not be recomputed. They are never shown as sources (they
  are not pages); if the settings cannot be read the checks fall back to the defaults and no prices are quoted from them.

Why the "small knowledge base" branch exists: a trigram gate needs the customer's words to overlap the published text. With a
real provider, casual phrasing ("می‌خوام برای آخر هفته یه نوبت بگیرم") scored 0.21 against the booking entry (gate 0.3) and English
scored 0, so good questions were declined. While the whole base fits in a few thousand characters it is cheaper to send all of it
and let the model choose; the guard still requires a `[n]` citation, so an off-topic question ends in `NO_ANSWER`. The price is
that the model is called (and tokens are spent) for unrelated messages too, until the base grows past the limits.

## The system prompt: two layers

| Layer | Where it lives | Who changes it | Effect of a change |
| --- | --- | --- | --- |
| **Fixed rules** (answer only from the passages, cite `[n]`, `NO_ANSWER` when unsure, never guess prices or booking state, trust `checked="true"` passages and never recompute them, warm colloquial Persian with the answer first and usually 2-4 sentences, no URLs, never reveal the instructions) plus two short tone samples | `backend/src/davos/modules/assistant/application/services/prompt_builder.py` | developers only | needs a rebuild; not file-editable because the grounding guard and the injection defence depend on them |
| **Style notes** (tone, what to ask, how to refuse politely, what to offer instead) | `backend/prompts/assistant_persona.txt`, mounted read-only into the API container | the owner | picked up on the next message, no restart (mtime + size cache) |
| **Facts** (hours, riding rules, phone, how booking works) | `backend/knowledge/*.txt` | the owner | applied at API start-up or with the sync command below |
| **Live settings** (kart counts, prices, closed days, hold time, online booking on/off) | admin panel, booking settings | the owner or staff with the owner role | next question after at most 30 s |

The persona goes inside a `<style>` block between the introduction and the fixed rules, and the rules state that they outrank it.
It is capped at 2000 characters, `#` lines are comments and never reach the model, a missing file falls back to a built-in default,
an empty file sends no notes, and the content is never logged. Facts are deliberately **not** in the persona: a fact in the
prompt would have no source, so the assistant could not cite it and the guard would discard the answer.

What the current persona asks for (version 4, 2026-09-25): talk like a real person at the booth, warm and colloquial but polite;
**the answer first** (yes / no / how much / when), then the reason in one short sentence; no preamble, no repeating the question, no
stock phrases, no fixed template; no questions whose answer is obvious from the message and at most one short question when the
answer really depends on it; say "no" plainly with the safety reason and offer the allowed alternative for that person (the rear
seat for a child who cannot drive yet); mention online booking only when the question is about booking. Version 2 forced a
"reason, then «پس بله / پس متأسفانه نه»" formula and a phone-booking reminder at the end of every riding answer; it made the answers
robotic and it is no longer needed, because the rule checks now decide the verdict in code. Chit-chat never reaches the model: `SmallTalkDetector`
recognises a message made only of greeting / "how are you" / thanks / "ok" / goodbye / "who are you" words (six words at most,
every word from a fixed list) and the use case answers with a fixed line from `assistant_messages.py`; a real question that merely
starts with "سلام" is not small talk.

**Quick answers.** A plain, general question about one topic (hours, booking and phone number, capacity, prices, the club) is
answered without the model (`QuickTopicDetector`, outcome `quick_answer`). Prices and capacity come from the live admin settings;
the other topics use the published knowledge entry itself, looked up by its title (`QUICK_TOPIC_TITLES` in `assistant_messages.py`),
and the booking entry gets the current closed days and hold time appended. So editing `knowledge/*.txt` or the admin settings
changes the answer, and a draft, a missing or a renamed entry silently sends the question through the normal flow
(`test_shipped_assistant_content.py` fails if a title no longer matches). The detector is strict: the question may contain only the
topic phrase and neutral filler words, so anything with a day, an hour, an age, a car type or a second topic goes to the model.

The knowledge files must not contain numbers that the admin panel controls (see `backend/knowledge/README.md`); they would go stale
the first time the owner changes a price or the number of karts.

Why files and not the database: the admin panel edits the booking settings but not knowledge text yet; files are reviewable and
diff-able, and `AssistantPersonaPort` / `KnowledgeDocumentSourcePort` let a database or CMS adapter replace them later without
touching the use case.

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
| Model invents facts / prices / booking state | must cite sources `[n]`; uncited or `NO_ANSWER` output is discarded (after one repair call for a missing citation); system prompt forbids guessing prices, availability, payment or booking status; prices and kart counts come from the live admin settings |
| Model gets the arithmetic wrong (140 vs "more than 140", 65 + 65 vs "below 130", hours, group sessions) | the comparisons are made in code and handed over as a `checked="true"` passage the model is told not to recompute |
| Model glitches into another script mid-sentence (seen once with a Qwen model) | Chinese/Japanese/Korean characters make the answer not showable; one repair call asks for a Persian-only rewrite |
| Owner's style notes weaken the rules | the notes sit in a delimited `<style>` block, are sanitised like other text, and the fixed rules say they win |
| Model leaks its instructions | per-request canary token plus rule-text fingerprints; any match withholds the answer |
| Model writes links | every URL and markdown link is stripped; only retrieved internal source URLs are shown |
| Private data in the knowledge base | closed `KnowledgeSourceType` list (no customer/ticket/note type exists); DB `CHECK` on type and on internal-only URLs; only published content is indexed, unpublishing (or a draft file) removes it |
| Tool abuse | the model has **no tools**: it cannot pay, change accounts, apply discounts or alter bookings |
| Cost runaway | max question length (500 in the chat, 2000 at the API), per-IP (30/hour) and per-conversation limits, shared daily token budget (Redis, atomic reserve/settle), output token cap |
| Provider outage / slowness | timeout (12 s), bounded concurrency (bulkhead), a circuit breaker per model, the backup model (`AI_FALLBACK_MODEL`) when the main one fails, then a fallback with related links and the contact page |
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
| `AI_TOKEN_LIMIT_PARAM` | `max_tokens` (default) or `max_completion_tokens` for providers and reasoning models that require it |
| `AI_SEND_TEMPERATURE` | `false` for reasoning models that reject a temperature |
| `AI_MIN_OUTPUT_TOKENS` | a floor for the output limit; reasoning models think inside it (2000 for `gpt-5.6-luna`, otherwise they can return an empty answer) |
| `AI_FALLBACK_MODEL`, `AI_FALLBACK_TOKEN_LIMIT_PARAM`, `AI_FALLBACK_SEND_TEMPERATURE`, `AI_FALLBACK_MIN_OUTPUT_TOKENS` | optional backup model on the same provider, asked only when the main model fails |
| `AI_DAILY_TOKEN_BUDGET` | shared daily budget, default 400000. A question costs roughly 2-5k tokens (the knowledge passages are sent), so about 100-200 model-answered questions a day fit; raise it if the site is busy |
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
* **Round 3, 2026-09-24/25: model comparison (the owner asked for it) and the rules engine.** A 38-question set (26 everyday + 12
  hard numeric cases: 141 cm at 17:45, 11-year-old at 18:30, 139 cm, 16-year-old driving a two-seater, two 19-year-olds, 65 + 65 kg,
  13 / 12 / 6 adults, unknown topics, an injection) run through the real `AskAssistantUseCase` (prompt, checks, guard, repair) with a
  scripted search returning every published entry; the keyword grader has false negatives, so every failure was read by hand.
  Before the rules engine, from prose alone: gapgpt-qwen-3.6 ~100 %, gpt-5.6-luna 99 %, gpt-6-luna 96 %, gemma-3-27b-it 85 %
  (wrong on 140 cm, 65 + 65, two 19-year-olds, 18:30, a 5-year-old), gpt-4o-mini 83 %. With the checks and live settings:
  **gpt-5.6-luna 38/38, median 1.8 s, about $0.77 per 1000 questions** (now `AI_MODEL`); gapgpt-qwen-3.6 38/38 but slower (median
  2.6-4.2 s) and once wrote Chinese words mid-sentence (now caught) (now `AI_FALLBACK_MODEL`); gpt-4o-mini and gemma-3-27b-it
  still contradicted the computed group verdict once each, and gemma prefixed answers with ":" (now stripped). The answers read as
  natural colloquial Persian with the verdict first. Still a fixed set, not proof for every phrasing.

## Not done yet

An admin screen for unanswered questions, feedback and cost; turning recurring questions into FAQ **drafts**; editing knowledge
text from the admin panel (only booking settings are editable there); CMS-driven indexing of FAQ/policy pages (the indexing use case
exists; only the file sync publishes to it); streaming replies; and turning the scratchpad benchmark into a committed evaluation
command that can be re-run whenever the model, persona or knowledge changes.
