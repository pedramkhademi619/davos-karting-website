from __future__ import annotations

from dataclasses import dataclass

from davos.tools.assistant_eval.expectation_kind import ExpectationKind


@dataclass(frozen=True)
class EvalCase:
    """One labelled question. ``history`` are earlier questions of the same conversation, asked first and not graded.

    ``must``: every group needs at least one of its alternatives in the reply (compared after GradingText
    normalisation, so "۷۹۰ هزار" matches "790000"). ``never``: none of these may appear.
    """

    case_id: str
    category: str
    question: str
    kind: ExpectationKind
    history: tuple[str, ...] = ()
    must: tuple[tuple[str, ...], ...] = ()
    never: tuple[str, ...] = ()
    note: str = ""
