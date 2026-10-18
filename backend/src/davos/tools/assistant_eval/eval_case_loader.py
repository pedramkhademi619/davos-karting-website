from __future__ import annotations

import json
from pathlib import Path

from davos.tools.assistant_eval.eval_case import EvalCase
from davos.tools.assistant_eval.expectation_kind import ExpectationKind


class EvalCaseLoader:
    """Reads the question set: one JSON object per line, ``#`` lines and blank lines ignored.

    Fields: id, category, question, kind (see ExpectationKind), and optionally history (list of earlier questions),
    must (list of lists of alternatives), never (list), note. Any mistake stops the run with the line number: a silently
    skipped case would make two runs incomparable. ``{NAME}`` in must/never is replaced from ``placeholders`` (the
    deployment's values, e.g. CONTACT_PHONE), so the question set never repeats a number that lives in .env.
    """

    def __init__(self, placeholders: dict[str, str] | None = None) -> None:
        self._placeholders = placeholders or {}

    def load(self, path: Path) -> list[EvalCase]:
        cases: list[EvalCase] = []
        seen: set[str] = set()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for name, value in self._placeholders.items():
                stripped = stripped.replace("{" + name + "}", value)
            try:
                case = self._parse(json.loads(stripped))
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"{path.name}:{number}: {exc}") from exc
            if case.case_id in seen:
                raise ValueError(f"{path.name}:{number}: duplicate id {case.case_id}")
            seen.add(case.case_id)
            cases.append(case)
        return cases

    @staticmethod
    def _parse(raw: dict[str, object]) -> EvalCase:
        must = raw.get("must", [])
        never = raw.get("never", [])
        history = raw.get("history", [])
        if not isinstance(must, list) or not all(isinstance(g, list) and g for g in must):
            raise TypeError("must is a list of non-empty lists")
        if not isinstance(never, list) or not isinstance(history, list):
            raise TypeError("never and history are lists")
        question = str(raw["question"]).strip()
        if not question:
            raise ValueError("empty question")
        return EvalCase(
            case_id=str(raw["id"]),
            category=str(raw["category"]),
            question=question,
            kind=ExpectationKind(str(raw["kind"])),
            history=tuple(str(h) for h in history),
            must=tuple(tuple(str(a) for a in group) for group in must),
            never=tuple(str(n) for n in never),
            note=str(raw.get("note", "")),
        )
