from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Sequence
from typing import Any

from davos.tools.assistant_eval.case_run import CaseRun
from davos.tools.assistant_eval.run_config import RunConfig
from davos.tools.assistant_eval.wilson_interval import WilsonInterval


def _percentile(values: Sequence[float], share: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(share * len(ordered)) - 1)]


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


class EvalReport:
    """Aggregates the runs of one evaluation into the numbers a comparison needs and renders them.

    Accuracy: pass rate over all runs with a 95 % Wilson interval, and pass^k, the share of questions answered right in
    every repeat (a customer does not get to retry). Cost: tokens per question, the share of prompt tokens served from
    the provider's cache, the provider-reported dollars per 1000 questions (questions answered without the model count
    as free), and the share of questions that needed a second (repair) call. Latency: whole pipeline, p50 and p95.
    """

    def __init__(self, runs: Sequence[CaseRun], config: RunConfig, meta: dict[str, str]) -> None:
        self._runs = list(runs)
        self._config = config
        self._meta = meta

    def summary(self) -> dict[str, Any]:
        runs = self._runs
        passed = sum(r.grade.passed for r in runs)
        low, high = WilsonInterval.of(passed, len(runs))
        by_case: dict[str, list[CaseRun]] = defaultdict(list)
        for run in runs:
            by_case[run.case.case_id].append(run)
        modelled = [r for r in runs if r.calls]
        calls = [c for r in runs for c in r.calls if not c.failed]
        prompt = sum(c.prompt_tokens for c in calls)
        cached = sum(c.cached_prompt_tokens for c in calls)
        costs = [r.cost_usd for r in runs]
        cost_known = all(c is not None for c in costs)
        judged = [r for r in runs if r.judge is not None]
        summary: dict[str, Any] = {
            **self._meta,
            "model": self._config.model,
            "label": self._config.label,
            "cases": len(by_case),
            "repeats": self._config.repeats,
            "runs": len(runs),
            "pass_rate": passed / len(runs) if runs else 0.0,
            "pass_rate_ci95": [low, high],
            # quality alone: runs where the provider failed say nothing about the prompt or the model's answers
            "pass_rate_without_provider_failures": self._rate([r for r in runs if not any(c.failed for c in r.calls)]),
            "pass_all_repeats": sum(all(r.grade.passed for r in rs) for rs in by_case.values()) / max(len(by_case), 1),
            "by_category": self._by_category(),
            "outcomes": dict(Counter(r.outcome for r in runs)),
            "model_answered_share": len(modelled) / len(runs) if runs else 0.0,
            "repair_share": sum(len(r.calls) > 1 for r in modelled) / len(modelled) if modelled else 0.0,
            "provider_failures": sum(c.failed for r in runs for c in r.calls),
            "mean_prompt_tokens": _mean([sum(c.prompt_tokens for c in r.calls) for r in modelled]),
            "mean_completion_tokens": _mean([sum(c.completion_tokens for c in r.calls) for r in modelled]),
            "cached_prompt_share": cached / prompt if prompt else 0.0,
            "usd_per_1000_questions": 1000 * sum(c or 0.0 for c in costs) / len(runs) if cost_known and runs else None,
            "latency_p50_s": _percentile([r.latency_s for r in modelled], 0.5),
            "latency_p95_s": _percentile([r.latency_s for r in modelled], 0.95),
        }
        if judged:
            summary["judge"] = {
                "judged": len(judged),
                "correct": sum(r.judge.correct for r in judged if r.judge) / len(judged),
                "faithful": sum(r.judge.faithful for r in judged if r.judge) / len(judged),
                "helpful": sum(r.judge.helpful for r in judged if r.judge) / len(judged),
                "natural": sum(r.judge.natural for r in judged if r.judge) / len(judged),
                "agreement_with_grader": sum(r.judge.correct == r.grade.passed for r in judged if r.judge)
                / len(judged),
            }
        return summary

    def rows(self) -> list[dict[str, Any]]:
        return [
            {
                "id": r.case.case_id,
                "category": r.case.category,
                "repeat": r.repeat,
                "question": r.case.question,
                "history": list(r.case.history),
                "kind": r.case.kind.value,
                "outcome": r.outcome,
                "passed": r.grade.passed,
                "reason": r.grade.reason,
                "verdict": r.grade.verdict.value,
                "answer": r.answer,
                "latency_s": round(r.latency_s, 2),
                "calls": [c.__dict__ for c in r.calls],
                "judge": r.judge.__dict__ if r.judge else None,
            }
            for r in self._runs
        ]

    def markdown(self) -> str:
        s = self.summary()
        low, high = s["pass_rate_ci95"]
        cost = s["usd_per_1000_questions"]
        lines = [
            f"# Assistant evaluation: {s['label'] or s['model']}",
            "",
            f"{s['date']} · model `{s['model']}` · commit `{s['commit']}` · rules `{s['rules_version']}` · "
            f"persona `{s['persona_sha']}` · knowledge `{s['knowledge_sha']}`",
            "",
            *(
                [f"**Stopped early: {s['aborted']}.** Only the questions answered before that are counted.", ""]
                if s.get("aborted")
                else []
            ),
            "| Metric | Value |",
            "| --- | --- |",
            f"| Questions × repeats | {s['cases']} × {s['repeats']} = {s['runs']} |",
            f"| Pass rate (95 % CI) | **{s['pass_rate']:.1%}** ({low:.1%} - {high:.1%}) |",
            f"| Pass rate without provider failures | {s['pass_rate_without_provider_failures']:.1%} |",
            f"| Right in every repeat (pass^k) | {s['pass_all_repeats']:.1%} |",
            f"| Answered by the model | {s['model_answered_share']:.1%} of questions |",
            f"| Needed a repair call | {s['repair_share']:.1%} of model-answered questions |",
            f"| Provider failures | {s['provider_failures']} |",
            f"| Prompt tokens per model-answered question | {self._num(s['mean_prompt_tokens'])} |",
            f"| Served from the provider cache | {s['cached_prompt_share']:.1%} of prompt tokens |",
            f"| Completion tokens per model-answered question | {self._num(s['mean_completion_tokens'])} |",
            f"| Cost per 1000 questions (provider-reported) | {'n/a' if cost is None else f'${cost:.3f}'} |",
            f"| Spent on this evaluation (answers + judge) | ${s.get('spent_usd') or '?'} |",
            f"| Latency p50 / p95 (model-answered) | {self._num(s['latency_p50_s'], 1)} s / "
            f"{self._num(s['latency_p95_s'], 1)} s |",
        ]
        judge = s.get("judge")
        if judge:
            lines += [
                f"| Judge `{s.get('judge_model', '')}`: correct / faithful / helpful / natural | "
                f"{judge['correct']:.0%} / {judge['faithful']:.0%} / {judge['helpful']:.0%} / {judge['natural']:.0%} "
                f"(of {judge['judged']}) |",
                f"| Judge agrees with the keyword grader | {judge['agreement_with_grader']:.0%} |",
            ]
        lines += ["", "## By category", "", "| Category | Passed | Rate |", "| --- | --- | --- |"]
        for category, (ok, total) in s["by_category"].items():
            lines.append(f"| {category} | {ok}/{total} | {ok / total:.0%} |")
        lines += ["", "## Outcomes", ""]
        lines += [f"- `{name}`: {count}" for name, count in sorted(s["outcomes"].items())]
        failures = [r for r in self._runs if not r.grade.passed]
        lines += ["", f"## Failures ({len(failures)})", ""]
        for r in failures:
            lines.append(f"- **{r.case.case_id}** (repeat {r.repeat}, {r.grade.reason}): {r.case.question}")
            lines.append(f"  - reply: {self._short(r.answer)}")
            if r.judge:
                lines.append(f"  - judge: correct={r.judge.correct}; {r.judge.rationale}")
        disagreements = [r for r in self._runs if r.judge and r.judge.correct != r.grade.passed and r.grade.passed]
        if disagreements:
            lines += ["", f"## Passed by the grader, judged wrong ({len(disagreements)})", ""]
            for r in disagreements:
                lines.append(f"- **{r.case.case_id}** (repeat {r.repeat}): {r.case.question}")
                lines.append(f"  - reply: {self._short(r.answer)}")
                lines.append(f"  - judge: {r.judge.rationale if r.judge else ''}")
        return "\n".join(lines) + "\n"

    def _by_category(self) -> dict[str, tuple[int, int]]:
        table: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for run in self._runs:
            table[run.case.category][0] += run.grade.passed
            table[run.case.category][1] += 1
        return {k: (v[0], v[1]) for k, v in sorted(table.items())}

    @staticmethod
    def _rate(runs: Sequence[CaseRun]) -> float:
        return sum(r.grade.passed for r in runs) / len(runs) if runs else 0.0

    @staticmethod
    def _num(value: float | None, digits: int = 0) -> str:
        return "n/a" if value is None else f"{value:.{digits}f}"

    @staticmethod
    def _short(text: str) -> str:
        flat = " ".join(text.split())
        return flat if len(flat) <= 260 else flat[:257] + "..."
