# Assistant evaluation

How the assistant's quality and cost are measured, so every change to the prompt, the persona, the knowledge files or the
model is judged by numbers instead of by a few hand-picked questions. Status: method and tooling done; the gemma results
are still to be run (see "Results").

## Question set

`backend/evals/assistant/cases.jsonl`: 106 labelled questions in 14 categories: single-seater age / height / day / hour
rules, two-seater rules, group planning, prices, booking rules, opening hours, capacity, the customer club, questions the
knowledge does not cover, off-topic questions, manipulation attempts, phrasing (English, Finglish, typos, rambling),
follow-ups in one conversation, and small talk. Each case has a label (`kind`): `yes` / `no` (the verdict must open the
reply), `venue` (the rules leave it open: never say yes, send the customer to the venue), `info` (facts that must appear),
`defer` (not in the knowledge: declining or pointing to the venue is right), `refuse`, `small_talk`; optional `must`
(facts, with alternatives), `never` (forbidden text) and `history` (earlier questions of the same conversation). Labels
follow `backend/knowledge` and the admin panel's initial settings; `{CONTACT_PHONE}` is filled from `.env`. Contested
labels were removed rather than guessed (for example whether 18:00 is inside "15 to 18").

## Method

`python -m davos.tools.evaluate_assistant` (run from the repository root; see its `--help`) sends every question through
the real `AskAssistantUseCase` (prompt, persona, rule checks, live-settings passage, grounding guard, citation repair,
conversation memory) with in-memory stand-ins for the database, Redis and the admin panel, and only the model called
for real. It is not an end-to-end test of the website: retrieval runs in the small-knowledge-base mode that production
uses today (every published entry is sent), so the trigram search is not what is measured.

* **Grading.** A deterministic grader reads the verdict from the reply's first sentence and checks the required and
  forbidden facts after normalising digits, letters and spelled-out amounts ("۷ میلیون و ۱۱۰ هزار" = 7110000). Keyword
  grading has false negatives, so every failure is listed with its reply, and an optional LLM judge (a model from the
  owner's allowed list, of another family than the one evaluated) gives a binary second opinion on correctness,
  faithfulness to the knowledge, helpfulness and natural Persian. Where the two disagree a person reads the reply.
  `--regrade` grades stored replies again after a grader or label fix, without calling a model.
* **Statistics.** Pass rate with a 95 % Wilson interval (honest for small samples and rates near 100 %), and pass^k, the
  share of questions answered right in every one of k repeats: a customer asks once.
* **Cost and speed.** Prompt, cached and completion tokens per question, the provider-reported cost per 1000 questions
  (questions answered without a model count as free), the share that needed a repair call, provider failures, and p50 /
  p95 latency of the whole pipeline.
* **Safety of the run.** A spending cap (`--max-cost`, default $1, answers and judge together) and an immediate stop when
  the provider rejects a request (bad key, unknown model, no credit), so a broken run never produces a misleading report.

## Findings so far

* **Prompt caching (2026-09-26/27, gpt-5.6-luna through GapGPT).** Providers cache a prompt prefix up to a message
  boundary. The old layout put a random per-request canary inside the system message and the knowledge, ordered by
  relevance, in the user message: 0 % of prompt tokens were served from the cache. The same prompt with everything
  question-independent (rules, persona, samples, the whole knowledge in a fixed order) in the system message and
  everything question-specific (computed checks, history, question, canary) in the user message: 99 % cached from the
  second question on, cost per question 0.00082 -> 0.00013 USD (-84 %). A random value at the end of the system message
  also defeated the cache, which is why the canary moved to the user message. Now in production
  (`PromptBuilder.build(..., shared=...)`); the live site showed about 87 % of prompt tokens cached. gemma-3-27b-it,
  the model now in use, gets no cache hits through the gateway, but costs about a fifteenth of gpt-5.6-luna per token.
* **Reasoning effort.** gpt-5.6-luna through the gateway reported 0 reasoning tokens at every `reasoning_effort`, so the
  setting changes nothing there.
* **First baseline (2026-09-27, gpt-5.6-luna, invalid as a whole).** The judge used then was not on the owner's model list
  and exhausted the account's credit half-way; 159 of 318 calls failed with "insufficient quota". Of the 159 valid
  replies 96.9 % passed, and 4 of the 5 failures were grader or label mistakes (fixed): "نه، مشکلی نیست" is a yes, and
  ignoring an injected fake price while quoting the real one is correct. The one real fault: advice about clothing that
  is only in a draft entry.

## Answer cache (2026-10-01, branch `feature/semantic-cache`)

`python -m davos.tools.evaluate_answer_cache [--verify]` runs the cache's own rules on `backend/evals/assistant/cache_pairs.jsonl`:
25 pairs of one question in two wordings, 36 look-alike pairs with different answers (online/by phone, regular/holiday,
cancel/book, minimum/maximum age, cash/instalments, hour/day, ...) and 6 pairs that must never be cached. It uses the real
embedding model and, with `--verify`, the real check by `gemma-3-27b-it`; a few cents.

* **Embedding similarity cannot separate them.** Paraphrases scored 0.23-0.95 and look-alikes 0.47-0.97 (cancel vs
  book fee 0.83, "active?" vs "what is it?" 0.91, minimum vs maximum age 0.97). At the threshold with no false hit, only 1
  of 25 paraphrases was served; after a stricter rule, 0. A first version of this cache (threshold 0.94) would have served
  "cash" for "instalments" (0.947) and "maximum age" for "minimum age" (0.968).
* **A check by the model, comparing the two questions, does.** Asked in both directions and required to agree, it rejected
  all 36 look-alikes (12 of which no other rule stopped, 16 after the second round of harder pairs) and confirmed 11 of 25
  paraphrases at floor 0.50 (16 at 0.40), at about 0.8 s. Comparing the *stored answer* with the new question was worse
  (6 false yes of 42: a holiday-price question accepted the normal-price reply), so that variant was not used.
* **Chosen settings:** threshold 0.99 (served without a check only above every look-alike seen), check from 0.50, check
  timeout 5 s. The 0.99 level was found by the second round of look-alikes; the first round alone suggested 0.94.
* **Live, local stack (gemma, 4 API workers):** a first question 4.9 s; the same words again 0.02 s; another wording of
  the same meaning 1.1 s from the cache; "by phone" asked after "online" was answered by the model, not reused; a question
  with an age, day and hour never cached. Memory: 307 MB per API worker with the model loaded (1.29 GB for four).
* **Not proven:** 36 look-alike pairs with 0 false yes bounds the check's false-yes rate only to roughly 8 % (95 %), and the
  pairs are one person's reading of what counts as "the same answer"; the check is gemma judging gemma's domain. The
  other rules (general question, signature, fingerprint, no policy answers) and the "not helpful" vote are the safety net.
  Set `SEMANTIC_CACHE_VERIFY_WITH_MODEL=false` to keep only near-identical text (threshold 0.99), or
  `SEMANTIC_CACHE_ENABLED=false` for no cache.

## Fixing the known faults (2026-10-01 to 10-04, branch `feature/semantic-cache`)

All numbers are `gemma-3-27b-it`, reports in `backend/evals/assistant/reports/`. The dev set grew to 127 cases while this work went on (a case was added for each fault found), so only runs on the same
file are comparable; the first two rows ran on its 124-case state.

| Run | Pass | Notes |
| --- | --- | --- |
| `2026-10-01_before-fixes` (124 cases) | 78.2 % | invented answers about things the knowledge never mentions: 19 % right |
| `2026-10-01_after-prompt-rule` (124) | 91.5 % | rule 8 in the system prompt: such questions answered with NO_ANSWER, 88 % right |
| `2026-10-04_dev_final2` (127, 2 repeats) | 98.0 %, pass^2 96.1 % | + rule-engine fixes, support check, label fixes; median 2.5 s, about $0.21 per 1000 questions |

* **Code now decides what a model kept getting wrong:** the cost of a group (9 adults: 9 x 790,000 = 7,110,000, the model
  had said 4,950,000), an adult with a child in the two-seater (a positive verdict), a 15 year old ("not settled, the
  venue decides", not "yes"), "are you open at 23:00 on Tuesday?" (hours compared with `working-hours.txt`; a test keeps
  the two in step), and follow-ups without details ("و قیمتش؟" after "۹ نفر بزرگسالیم") are checked with the previous
  question's people.
* **The prompt rule is contaminated on the dev set.** Rule 8 first listed topics that the dev questions also use. They were
  replaced by unrelated ones (wifi, prayer room, taxi, locker, cake), and two new sets were written, set A
  (`cases_held_out.jsonl`, 24 questions) and set B (`cases_held_out_b.jsonl`, 12 questions, written before the change under
  test was measured and never used to change the prompt).
* **Honest held-out result.** Set A first gave 75 % (the model answered "no, not possible" about things the knowledge
  does not say, e.g. instalments, wheelchairs). The sentence "not written in the sources means *I do not know*, not *we do
  not have it*" was added; that set was then used once to tune, so its later 95.8 % is not held-out. **Set B: 30.6 % with the
  prompt rules alone.** Prompting alone does not generalise.
* **Support check** (`AnswerSupportVerifier`): after the guard, a second tiny request gets the cited sources plus the
  computed passages and the answer, and says YES/NO to "does everything the answer states appear in them?". It does not
  run when the budget is spent or the call fails (the answer is shown as before). **Set B: 30.6 % -> 55.6 %.** 6 of the
  12 questions still fail in at least one run. Reading the replies: 3 are defensible answers that the keyword label is too
  strict about (a rear-seat age range for "age for a companion", "minimum group size is not fixed"), 2 are partly grounded
  ("we have no card-to-card number, payment is through the gateway"; "no ID card is asked, booking needs a mobile number"),
  and 1 is a plain invention ("we have no system for lap records").
  The extra call costs about 0.00004-0.0001 USD and 1-3 s on answers that reach the model.
* **The check's price in wrong blocks:** first version blocked 6 of 254 correct dev answers (2.4 %: it read "the model also
  said *your daughter*" and "sit as a passenger in the back" as unsupported); telling it that facts the customer stated and
  rewordings of a source count as supported removed 5 of the 6. The one answer that stayed blocked every time was the 14 year old at 21:00 (right verdict plus a rear-seat
  suggestion), and the live site showed it: "no confirmed information" instead of "no". So the check is skipped when the rule
  engine computed a verdict for the question (age, height, day, hour, group): code already decided it and the model only words
  it. Dev 97.6 % -> 98.0 %, set B unchanged at 55.6 % (the set has no such questions); live, both 14 year old sentences answer
  correctly and are never cached.
* **Grader fixes:** an answer such as "it is not in the sources" or "I have no access" now counts as declining in `defer` and
  `refuse` cases; price-02 and single-12 accept the other correct wordings ("یک میلیون و دویست", "۳ تا ۶ بعدازظهر");
  attack-03/05 labels no longer punish a refusal for repeating the fake price it refuses.
* **Provider noise:** on 2026-10-04 the gateway was intermittently slow (calls above 12 s). Those runs were thrown away and
  repeated with `--timeout 20`; a failed provider call counts as a failure in "pass", the line "without provider
  failures" shows the rest.
* **Not proven:** 12 held-out questions cannot bound the invention rate tightly (a Wilson interval on 20/36 runs is roughly
  40-70 %), and the keyword labels of the unknown-topic cases are my reading. A bigger held-out set, written by the owner
  from real customer questions, is the next step.

## Results

To be filled from `backend/evals/assistant/reports/` once gemma-3-27b-it has been evaluated and tuned. Known issue to
start with: gemma sometimes writes grouped citations such as "[10, 11]" or "[10، 11]", which the guard leaves in the
visible text.

## Limits

A fixed question set is not proof for every phrasing; the labels are one person's reading of the owner's rules; the
keyword grader and the judge can both be wrong, which is why disagreements are read by hand. Latency depends on the
gateway's load at the time of the run.
