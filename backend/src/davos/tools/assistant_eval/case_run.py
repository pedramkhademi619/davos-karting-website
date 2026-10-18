from __future__ import annotations

from dataclasses import dataclass

from davos.tools.assistant_eval.case_grade import CaseGrade
from davos.tools.assistant_eval.eval_case import EvalCase
from davos.tools.assistant_eval.judge_verdict import JudgeVerdict
from davos.tools.assistant_eval.model_call import ModelCall


@dataclass(frozen=True)
class CaseRun:
    """One evaluated question in one repeat: the reply, its grade and what answering it cost."""

    case: EvalCase
    repeat: int
    answer: str
    outcome: str
    grade: CaseGrade
    calls: tuple[ModelCall, ...]
    latency_s: float
    judge: JudgeVerdict | None = None

    @property
    def cost_usd(self) -> float | None:
        costs = [c.cost_usd for c in self.calls]
        if any(c is None for c in costs):
            return None
        return sum(c for c in costs if c is not None)
