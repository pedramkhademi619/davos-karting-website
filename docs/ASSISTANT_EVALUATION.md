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

## Results

To be filled from `backend/evals/assistant/reports/` once gemma-3-27b-it has been evaluated and tuned. Known issue to
start with: gemma sometimes writes grouped citations such as "[10, 11]" or "[10، 11]", which the guard leaves in the
visible text.

## Limits

A fixed question set is not proof for every phrasing; the labels are one person's reading of the owner's rules; the
keyword grader and the judge can both be wrong, which is why disagreements are read by hand. Latency depends on the
gateway's load at the time of the run.
