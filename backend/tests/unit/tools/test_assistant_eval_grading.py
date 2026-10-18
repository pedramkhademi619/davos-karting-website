from __future__ import annotations

from pathlib import Path

import pytest

from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.tools.assistant_eval.case_grader import CaseGrader
from davos.tools.assistant_eval.eval_case import EvalCase
from davos.tools.assistant_eval.eval_case_loader import EvalCaseLoader
from davos.tools.assistant_eval.expectation_kind import ExpectationKind
from davos.tools.assistant_eval.grading_text import GradingText
from davos.tools.assistant_eval.verdict import Verdict
from davos.tools.assistant_eval.verdict_classifier import VerdictClassifier
from davos.tools.assistant_eval.wilson_interval import WilsonInterval

SHIPPED_CASES = Path(__file__).resolve().parents[3] / "evals" / "assistant" / "cases.jsonl"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("۷ میلیون و ۱۱۰ هزار تومان", "7110000 تومان"),
        ("۷٬۱۱۰٬۰۰۰ تومان", "7110000 تومان"),
        ("یک میلیون و ۲۰۰ هزار", "1200000"),
        ("۷۹۰ هزار تومن", "790000 تومن"),
        ("نمی‌تونه", "نمیتونه"),
        ("Can NOT", "can not"),
    ],
)
def test_grading_text_makes_amounts_digits_and_letters_comparable(text: str, expected: str) -> None:
    assert GradingText.normalize(text) == expected


@pytest.mark.parametrize(
    ("reply", "verdict"),
    [
        ("آره، می‌تونه! قدش از حداقل بیشتره [1].", Verdict.YES),
        ("بله، به شرط اینکه گواهینامه داشته باشید [1].", Verdict.YES),
        ("نه، نمی‌تونه؛ ساعت ۱۹ خارج از بازه است [1].", Verdict.NO),
        ("متأسفانه نه؛ صندلی عقب مخصوص بچه‌هاست [1].", Verdict.NO),
        ("نه!\nچون زیر ۱۱ سال رانندگی ممنوعه [1].", Verdict.NO),
        ("بچه نه ساله نمی‌تونه برونه [1].", Verdict.NO),
        ("نه، مشکلی نیست؛ می‌تونید تک‌نفره برونید [1].", Verdict.YES),
        ("برای ۱۵ ساله‌ها باید با مجموعه هماهنگ کنید [1].", Verdict.UNCLEAR),
        ("قدش ۱۵۰ است و روز شنبه است. آره می‌تونه.", Verdict.UNCLEAR),
    ],
)
def test_the_verdict_is_read_from_the_first_sentence(reply: str, verdict: Verdict) -> None:
    assert VerdictClassifier().classify(reply) is verdict


def case(kind: ExpectationKind, **fields: object) -> EvalCase:
    return EvalCase(case_id="c", category="t", question="q", kind=kind, **fields)  # type: ignore[arg-type]


def test_a_yes_case_needs_an_answered_yes_and_the_required_facts() -> None:
    grader = CaseGrader()
    yes = case(ExpectationKind.YES, must=(("15",),))
    assert grader.grade(yes, AnswerOutcome.ANSWERED, "آره، از ساعت ۱۵ تا ۱۸ [1].").passed
    assert not grader.grade(yes, AnswerOutcome.ANSWERED, "آره، می‌تونه [1].").passed
    assert not grader.grade(yes, AnswerOutcome.ANSWERED, "نه، ساعت ۱۵ نه [1].").passed
    assert not grader.grade(yes, AnswerOutcome.INSUFFICIENT_INFORMATION, "").passed


def test_forbidden_text_fails_any_case() -> None:
    grade = CaseGrader().grade(case(ExpectationKind.INFO, never=("رایگان",)), AnswerOutcome.ANSWERED, "رایگان است [1].")
    assert not grade.passed and "رایگان" in grade.reason


def test_a_refusal_is_right_for_off_topic_and_a_provider_failure_never_passes() -> None:
    grader = CaseGrader()
    refuse = case(ExpectationKind.REFUSE)
    assert grader.grade(refuse, AnswerOutcome.INSUFFICIENT_INFORMATION, "...").passed
    assert grader.grade(refuse, AnswerOutcome.REFUSED_UNSAFE_INPUT, "...").passed
    assert not grader.grade(refuse, AnswerOutcome.ANSWERED, "قیمت امروز ۲ میلیارد است [1].").passed
    assert not grader.grade(refuse, AnswerOutcome.FALLBACK_PROVIDER_UNAVAILABLE, "...").passed


def test_venue_cases_must_not_say_yes_and_must_point_to_the_venue() -> None:
    grader = CaseGrader()
    venue = case(ExpectationKind.VENUE)
    assert grader.grade(venue, AnswerOutcome.ANSWERED, "برای ۱۵ ساله‌ها باید با مجموعه هماهنگ کنید [1].").passed
    assert not grader.grade(venue, AnswerOutcome.ANSWERED, "آره، می‌تونه؛ فقط هماهنگ کنید [1].").passed


def test_wilson_interval_stays_inside_zero_and_one() -> None:
    low, high = WilsonInterval.of(100, 100)
    assert 0.96 < low < 1.0 and high == 1.0
    assert WilsonInterval.of(0, 0) == (0.0, 0.0)


def test_the_shipped_question_set_loads_and_every_yes_no_case_is_unambiguous() -> None:
    cases = EvalCaseLoader().load(SHIPPED_CASES)
    assert len(cases) >= 100
    assert len({c.case_id for c in cases}) == len(cases)


def test_the_loader_reports_the_line_of_a_broken_case(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text('# comment\n{"id": "a", "category": "x", "question": "q", "kind": "maybe"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match=r"cases\.jsonl:2"):
        EvalCaseLoader().load(path)
