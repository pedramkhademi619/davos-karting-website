"""Measure the answer cache on labelled question pairs and recommend the similarity threshold.

Run from the repository root (it reads SEMANTIC_CACHE_MODEL_DIR and the number of threads from .env):

    backend/.venv/Scripts/python.exe -m davos.tools.evaluate_answer_cache
    ... --pairs backend/evals/assistant/cache_pairs.jsonl --out backend/evals/assistant/reports
    ... --verify        # also ask the configured language model (AI_MODEL) the cache's check; a few cents at most

The pairs are run through the same rules as production: is each question cacheable (no age, day, hour, weight,
group size, follow-up or personal data), do the two share a signature, and how similar are their meanings for the
real embedding model. The report says, for every threshold, how many paraphrases would be answered from the cache
and how many look-alike questions with a different answer would be served by mistake (which must be none). No
language model is called unless --verify is given: then it is asked the cache's own check on every pair that passes
the other rules (two tiny requests each). Method: docs/ASSISTANT_EVALUATION.md.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

from davos.modules.assistant.adapters.ai.openai_compatible_chat_adapter import OpenAICompatibleChatAdapter
from davos.modules.assistant.adapters.budget.in_memory_ai_budget import InMemoryAiBudget
from davos.modules.assistant.adapters.embedding.onnx_sentence_embedding import OnnxSentenceEmbedding
from davos.modules.assistant.application.services.question_equivalence_verifier import QuestionEquivalenceVerifier
from davos.platform.clock.system_clock import SystemClock
from davos.platform.settings.app_settings import AppSettings
from davos.tools.cache_eval.cache_pair_evaluator import CachePairEvaluator
from davos.tools.cache_eval.cache_pair_loader import CachePairLoader
from davos.tools.cache_eval.cache_report import CacheReport

_BACKEND = Path(__file__).resolve().parents[3]
_MAX_TOKENS = 200_000  # a ceiling for one run (about 100 checks use 30,000)


def _verifier(settings: AppSettings, client: httpx.AsyncClient) -> QuestionEquivalenceVerifier:
    """The same check the API runs, against the configured model; a spending ceiling guards the run."""
    chat = OpenAICompatibleChatAdapter(
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key.get_secret_value(),
        model=settings.ai_model,
        http_client=client,
        timeout_seconds=settings.semantic_cache_verify_timeout_seconds,
        token_limit_param=settings.ai_token_limit_param,
        send_temperature=settings.ai_send_temperature,
        min_output_tokens=settings.ai_min_output_tokens,
    )
    budget = InMemoryAiBudget(daily_limit=_MAX_TOKENS, clock=SystemClock())
    return QuestionEquivalenceVerifier(
        chat=chat, budget=budget, timeout_seconds=settings.semantic_cache_verify_timeout_seconds
    )


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure the answer cache on labelled question pairs.")
    parser.add_argument("--pairs", type=Path, default=_BACKEND / "evals" / "assistant" / "cache_pairs.jsonl")
    parser.add_argument("--out", type=Path, default=_BACKEND / "evals" / "assistant" / "reports")
    parser.add_argument("--model-dir", help="default: SEMANTIC_CACHE_MODEL_DIR")
    parser.add_argument("--verify", action="store_true", help="also run the model check (needs AI_BASE_URL/KEY/MODEL)")
    return parser.parse_args()


async def _run() -> int:
    args = _arguments()
    settings = AppSettings()
    model_dir = args.model_dir or settings.semantic_cache_model_dir
    embedding = OnnxSentenceEmbedding(model_dir, threads=settings.semantic_cache_threads)
    await embedding.warm_up()
    try:
        await embedding.embed_query("test")
    except Exception:
        print(
            f"The embedding model could not be loaded from {model_dir!r}; "
            "fetch it with davos.tools.fetch_embedding_model."
        )
        return 2
    async with httpx.AsyncClient() as client:
        verifier = _verifier(settings, client) if args.verify else None
        results = await CachePairEvaluator(embedding, verifier).evaluate(CachePairLoader().load(args.pairs))
    report = CacheReport(
        results,
        model=embedding.model_name,
        date=datetime.now(UTC).strftime("%Y-%m-%d"),
        threshold=settings.semantic_cache_similarity_threshold,
        floor=settings.semantic_cache_verify_from_similarity,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    suffix = "_with-check" if args.verify else ""
    target = args.out / f"{datetime.now(UTC).strftime('%Y-%m-%d')}_answer-cache{suffix}.md"
    target.write_text(report.markdown(), encoding="utf-8")
    recommended = report.recommended_threshold()
    print(
        f"without the check, threshold {recommended:.2f}: paraphrases answered {len(report.hits(recommended))}, "
        f"false hits {len(report.false_hits(recommended))}, uncacheable touched {len(report.uncacheable_touched())}"
    )
    if args.verify:
        threshold = settings.semantic_cache_similarity_threshold
        floor = settings.semantic_cache_verify_from_similarity
        print(
            f"with the check (threshold {threshold:.2f}, from {floor:.2f}): paraphrases answered "
            f"{len(report.hits(threshold, floor))}, false hits {len(report.false_hits(threshold, floor))}"
        )
    print(f"report: {target}")
    return 0


def main() -> None:
    sys.exit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
