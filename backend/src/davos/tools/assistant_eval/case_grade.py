from __future__ import annotations

from dataclasses import dataclass

from davos.tools.assistant_eval.verdict import Verdict


@dataclass(frozen=True)
class CaseGrade:
    passed: bool
    reason: str  # "ok" or why it failed, short enough for a report table
    verdict: Verdict = Verdict.UNCLEAR
