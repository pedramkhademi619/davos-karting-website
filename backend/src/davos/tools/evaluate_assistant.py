"""Evaluate the assistant on the labelled question set and write a report.

Run from the repository root (AI_BASE_URL and AI_API_KEY come from .env; the key is never printed):

    backend/.venv/Scripts/python.exe -m davos.tools.evaluate_assistant --repeats 3 --label baseline
    ... --model gapgpt-qwen-3.6 --token-limit-param max_tokens --min-output-tokens 0
    ... --judge-model deepseek-reasoner        # adds an LLM judge's second opinion (allowed models only)
    ... --only prices,groups                   # a subset of categories (or case ids)
    ... --regrade backend/evals/assistant/reports/<file>.json   # grade stored replies again, no model calls

Without --model the settings' AI_MODEL is evaluated with its own token settings. Reports go to
backend/evals/assistant/reports/<date>_<label>.md and .json. Method: docs/ASSISTANT_EVALUATION.md.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

from davos.composition.adapters.schedule_booking_facts import ScheduleBookingFacts
from davos.composition.policy_factory import PolicyFactory
from davos.modules.assistant.adapters.ai.openai_compatible_chat_adapter import OpenAICompatibleChatAdapter
from davos.modules.assistant.adapters.knowledge.text_file_knowledge_source import TextFileKnowledgeSource
from davos.modules.assistant.adapters.persona.file_assistant_persona import FileAssistantPersona
from davos.modules.assistant.application.services.booking_facts_passage import BookingFactsPassage
from davos.modules.assistant.application.services.prompt_builder import PromptBuilder
from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.platform.settings.app_settings import AppSettings
from davos.tools.assistant_eval.case_grader import CaseGrader
from davos.tools.assistant_eval.case_run import CaseRun
from davos.tools.assistant_eval.eval_case_loader import EvalCaseLoader
from davos.tools.assistant_eval.eval_report import EvalReport
from davos.tools.assistant_eval.eval_runner import EvalRunner
from davos.tools.assistant_eval.file_knowledge_search import FileKnowledgeSearch
from davos.tools.assistant_eval.fixed_booking_facts import FixedBookingFacts
from davos.tools.assistant_eval.judge_verdict import JudgeVerdict
from davos.tools.assistant_eval.llm_judge import LlmJudge
from davos.tools.assistant_eval.model_call import ModelCall
from davos.tools.assistant_eval.run_config import RunConfig

_BACKEND = Path(__file__).resolve().parents[3]


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the assistant on the labelled question set.")
    parser.add_argument("--cases", type=Path, default=_BACKEND / "evals" / "assistant" / "cases.jsonl")
    parser.add_argument("--knowledge", type=Path, default=_BACKEND / "knowledge")
    parser.add_argument("--persona", type=Path, default=_BACKEND / "prompts" / "assistant_persona.txt")
    parser.add_argument("--out", type=Path, default=_BACKEND / "evals" / "assistant" / "reports")
    parser.add_argument("--model", help="model id; default AI_MODEL with its own token settings")
    parser.add_argument("--token-limit-param", choices=["max_tokens", "max_completion_tokens"])
    parser.add_argument("--no-temperature", action="store_true", help="for reasoning models that reject one")
    parser.add_argument("--min-output-tokens", type=int)
    parser.add_argument("--timeout", type=float, help="seconds per call; default AI_TIMEOUT_SECONDS")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--judge-model", help="a second, stronger model that grades the replies too")
    parser.add_argument("--only", help="comma-separated categories or case ids")
    parser.add_argument(
        "--no-support-check", action="store_true", help="skip the answer support check (measures what it adds)"
    )
    parser.add_argument("--label", default="")
    parser.add_argument("--judge-repeats", type=int, default=1, help="how many repeats the judge reads")
    parser.add_argument("--max-cost", type=float, default=1.0, help="USD; stop once the reported spend passes it")
    parser.add_argument("--regrade", type=Path, help="a report .json: grade its stored replies again and rewrite it")
    return parser.parse_args()


def _config(args: argparse.Namespace, settings: AppSettings) -> RunConfig:
    own = args.model in (None, settings.ai_model)
    return RunConfig(
        model=args.model or settings.ai_model,
        token_limit_param=args.token_limit_param or (settings.ai_token_limit_param if own else "max_tokens"),
        send_temperature=not args.no_temperature and (settings.ai_send_temperature if own else True),
        min_output_tokens=args.min_output_tokens
        if args.min_output_tokens is not None
        else (settings.ai_min_output_tokens if own else 0),
        timeout_seconds=args.timeout or settings.ai_timeout_seconds,
        repeats=args.repeats,
        concurrency=args.concurrency,
        label=args.label,
        max_cost_usd=args.max_cost,
        judge_repeats=args.judge_repeats,
        support_check=settings.ai_support_check_enabled and not args.no_support_check,
    )


def _sha(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]


def _git(*command: str) -> str:
    try:
        return subprocess.run(  # noqa: S603 - fixed git arguments
            ["git", *command],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
            cwd=_BACKEND,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _progress(run: CaseRun) -> None:
    mark = "ok  " if run.grade.passed else "FAIL"
    print(f"  {mark} {run.case.case_id:<22} r{run.repeat} {run.latency_s:5.1f}s {run.grade.reason}", flush=True)


async def _run() -> int:
    args = _arguments()
    if args.regrade:
        return _regrade(args.regrade, args.cases)
    settings = AppSettings()
    if not (settings.ai_base_url and settings.ai_api_key.get_secret_value()):
        print("AI_BASE_URL and AI_API_KEY must be set (in .env) to evaluate the assistant.")
        return 2
    config = _config(args, settings)
    cases = EvalCaseLoader({"CONTACT_PHONE": settings.contact_phone}).load(args.cases)
    if args.only:
        wanted = {w.strip() for w in args.only.split(",")}
        cases = [c for c in cases if c.case_id in wanted or c.category in wanted]
    documents = [d for d in TextFileKnowledgeSource(args.knowledge).read_all().documents if d.published]
    persona = FileAssistantPersona(str(args.persona))
    # the admin panel's initial settings: the question set's expected prices and kart counts assume them
    facts = ScheduleBookingFacts.from_settings(ScheduleSettings(), contact_phone=settings.contact_phone)
    knowledge_text = "\n\n".join(f"## {d.title}\n{d.body}" for d in documents)
    judge_knowledge = f"{knowledge_text}\n\n## Live booking settings\n{BookingFactsPassage().passage(facts).text}"
    dirty = "+dirty" if _git("status", "--porcelain", "--untracked-files=no") else ""
    meta = {
        "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "commit": _git("rev-parse", "--short", "HEAD") + dirty,
        "rules_version": PromptBuilder.rules_version(),
        "persona_sha": _sha(persona.text()),
        "knowledge_sha": _sha(knowledge_text),
        "judge_model": args.judge_model or "",
    }
    print(f"{len(cases)} questions x {config.repeats} with {config.model} ({config.label or 'no label'})")

    async with httpx.AsyncClient() as client:

        def adapter(model: str, token_limit_param: str, temperature: bool, floor: int) -> OpenAICompatibleChatAdapter:
            return OpenAICompatibleChatAdapter(
                base_url=settings.ai_base_url,
                api_key=settings.ai_api_key.get_secret_value(),
                model=model,
                http_client=client,
                timeout_seconds=config.timeout_seconds,
                token_limit_param=token_limit_param,
                send_temperature=temperature,
                min_output_tokens=floor,
            )

        judge = (
            LlmJudge(adapter(args.judge_model, "max_tokens", True, 0), judge_knowledge) if args.judge_model else None
        )
        runner = EvalRunner(
            config=config,
            chat=adapter(config.model, config.token_limit_param, config.send_temperature, config.min_output_tokens),
            search=FileKnowledgeSearch(TextFileKnowledgeSource(args.knowledge)),
            persona=persona,
            booking_facts=FixedBookingFacts(facts),
            policy=PolicyFactory.assistant(settings),
            judge=judge,
            grader=CaseGrader(contact_phone=settings.contact_phone),
            progress=_progress,
        )
        runs = await runner.run(cases)
    meta["spent_usd"] = f"{runner.spent_usd:.4f}"
    meta["aborted"] = runner.aborted
    if runner.aborted:
        print(f"STOPPED EARLY: {runner.aborted}. The report covers only the questions answered before that.")

    stem = f"{datetime.now(UTC).strftime('%Y-%m-%d')}_{config.label or config.model}".replace(" ", "-")
    _write(EvalReport(runs, config, meta), args.out / stem)
    return 0


def _write(report: EvalReport, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".md").write_text(report.markdown(), encoding="utf-8")
    payload = {"summary": report.summary(), "runs": report.rows()}
    stem.with_suffix(".json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = report.summary()
    print(
        f"pass {summary['pass_rate']:.1%} (without provider failures "
        f"{summary['pass_rate_without_provider_failures']:.1%})  pass^k {summary['pass_all_repeats']:.1%}  "
        f"cache {summary['cached_prompt_share']:.0%}  $/1000q {summary['usd_per_1000_questions']}  "
        f"p50 {summary['latency_p50_s']}s  -> {stem}.md"
    )


def _regrade(path: Path, cases_path: Path) -> int:
    """Grade the replies stored in a report again with the current grader and labels (no model is called)."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    summary = payload["summary"]
    settings = AppSettings()
    cases = {c.case_id: c for c in EvalCaseLoader({"CONTACT_PHONE": settings.contact_phone}).load(cases_path)}
    grader = CaseGrader(contact_phone=settings.contact_phone)
    runs = [
        CaseRun(
            case=cases[row["id"]],
            repeat=row["repeat"],
            answer=row["answer"],
            outcome=row["outcome"],
            grade=grader.grade(cases[row["id"]], AnswerOutcome(row["outcome"]), row["answer"]),
            calls=tuple(ModelCall(**call) for call in row["calls"]),
            latency_s=row["latency_s"],
            judge=JudgeVerdict(**row["judge"]) if row["judge"] else None,
        )
        for row in payload["runs"]
        if row["id"] in cases
    ]
    config = RunConfig(model=summary["model"], repeats=summary["repeats"], label=summary["label"])
    keys = ("date", "commit", "rules_version", "persona_sha", "knowledge_sha", "spent_usd", "aborted")
    meta = {k: str(summary.get(k, "")) for k in keys}
    meta["judge_model"] = summary.get("judge_model", "")
    _write(EvalReport(runs, config, meta), path.with_suffix(""))
    return 0


def main() -> None:
    sys.exit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
