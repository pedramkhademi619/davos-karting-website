"""Measure the answer cache on labelled question pairs and recommend the similarity threshold.

Run from the repository root (it reads SEMANTIC_CACHE_MODEL_DIR and the number of threads from .env):

    backend/.venv/Scripts/python.exe -m davos.tools.evaluate_answer_cache
    ... --pairs backend/evals/assistant/cache_pairs.jsonl --out backend/evals/assistant/reports

The pairs are run through the same rules as production: is each question cacheable (no age, day, hour, weight,
group size, follow-up or personal data), do the two share a signature, and how similar are their meanings for the
real embedding model. The report says, for every threshold, how many paraphrases would be answered from the cache
and how many look-alike questions with a different answer would be served by mistake (which must be none). No
language model is called: the run is free. Method: docs/ASSISTANT_EVALUATION.md.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

from davos.modules.assistant.adapters.embedding.onnx_sentence_embedding import OnnxSentenceEmbedding
from davos.platform.settings.app_settings import AppSettings
from davos.tools.cache_eval.cache_pair_evaluator import CachePairEvaluator
from davos.tools.cache_eval.cache_pair_loader import CachePairLoader
from davos.tools.cache_eval.cache_report import CacheReport

_BACKEND = Path(__file__).resolve().parents[3]


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure the answer cache on labelled question pairs.")
    parser.add_argument("--pairs", type=Path, default=_BACKEND / "evals" / "assistant" / "cache_pairs.jsonl")
    parser.add_argument("--out", type=Path, default=_BACKEND / "evals" / "assistant" / "reports")
    parser.add_argument("--model-dir", help="default: SEMANTIC_CACHE_MODEL_DIR")
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
    results = await CachePairEvaluator(embedding).evaluate(CachePairLoader().load(args.pairs))
    report = CacheReport(results, model=embedding.model_name, date=datetime.now(UTC).strftime("%Y-%m-%d"))
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / f"{datetime.now(UTC).strftime('%Y-%m-%d')}_answer-cache.md"
    target.write_text(report.markdown(), encoding="utf-8")
    recommended = report.recommended_threshold()
    print(
        f"recommended threshold {recommended:.2f}: paraphrases answered {len(report.hits(recommended))}, "
        f"false hits {len(report.false_hits(recommended))}, uncacheable touched {len(report.uncacheable_touched())} "
        f"-> {target}"
    )
    return 0


def main() -> None:
    sys.exit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
