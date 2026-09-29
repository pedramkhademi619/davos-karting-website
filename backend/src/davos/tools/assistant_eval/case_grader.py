from __future__ import annotations

from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.tools.assistant_eval.case_grade import CaseGrade
from davos.tools.assistant_eval.eval_case import EvalCase
from davos.tools.assistant_eval.expectation_kind import ExpectationKind
from davos.tools.assistant_eval.grading_text import GradingText
from davos.tools.assistant_eval.verdict import Verdict
from davos.tools.assistant_eval.verdict_classifier import VerdictClassifier

_ANSWERED = frozenset({AnswerOutcome.ANSWERED, AnswerOutcome.QUICK_ANSWER})
_DECLINED = frozenset({AnswerOutcome.INSUFFICIENT_INFORMATION, AnswerOutcome.REFUSED_UNSAFE_INPUT})
_FAILED = frozenset({AnswerOutcome.FALLBACK_PROVIDER_UNAVAILABLE, AnswerOutcome.FALLBACK_BUDGET_EXHAUSTED})
# A grounded reply that still declines ("این رو نمی‌دونم، از تماس با ما بپرسید") is a correct refusal.
_DECLINE_MARKERS = ("اطلاعاتی ندارم", "اطلاعی ندارم", "نمیدونم", "نمیدانم", "در منابع", "تماس با ما")
_CONTACT_WORDS = ("تماس", "هماهنگ", "پشتیبانی")


class CaseGrader:
    """Deterministic grading against the case's label. Keyword grading has false negatives (a correct reply worded
    unexpectedly), so every failure is listed in the report with the reply, and the optional LLM judge gives a second
    opinion; it has few false positives because a yes/no case needs the right verdict in the first sentence."""

    def __init__(self, *, contact_phone: str = "", classifier: VerdictClassifier | None = None) -> None:
        self._classifier = classifier or VerdictClassifier()
        # sending the customer to the venue: the contact words, or the venue's number (CONTACT_PHONE)
        self._contact_markers = (*_CONTACT_WORDS, contact_phone) if contact_phone else _CONTACT_WORDS

    def grade(self, case: EvalCase, outcome: AnswerOutcome, text: str) -> CaseGrade:
        verdict = self._classifier.classify(text) if outcome in _ANSWERED else Verdict.UNCLEAR
        if outcome in _FAILED:
            return CaseGrade(False, f"no model answer ({outcome.value})", verdict)
        normalized = GradingText.normalize(text)
        for forbidden in case.never:
            if GradingText.normalize(forbidden) in normalized:
                return CaseGrade(False, f"said «{forbidden}»", verdict)

        kind = case.kind
        if kind is ExpectationKind.SMALL_TALK:
            ok = outcome is AnswerOutcome.SMALL_TALK
            return CaseGrade(ok, "ok" if ok else f"expected small talk, got {outcome.value}", verdict)
        if kind is ExpectationKind.REFUSE:
            ok = outcome in _DECLINED or any(m in normalized for m in _DECLINE_MARKERS)
            return CaseGrade(ok, "ok" if ok else "answered instead of declining", verdict)
        if kind is ExpectationKind.DEFER:
            if outcome in _DECLINED:
                return CaseGrade(True, "ok", verdict)
            markers = [a for group in case.must for a in group] or list(self._contact_markers)
            ok = any(GradingText.normalize(m) in normalized for m in markers)
            return CaseGrade(ok, "ok" if ok else "answered without deferring to the venue", verdict)

        if outcome not in _ANSWERED:
            return CaseGrade(False, f"not answered ({outcome.value})", verdict)
        if kind is ExpectationKind.YES and verdict is not Verdict.YES:
            return CaseGrade(False, f"expected yes, reply opens with {verdict.value}", verdict)
        if kind is ExpectationKind.NO and verdict is not Verdict.NO:
            return CaseGrade(False, f"expected no, reply opens with {verdict.value}", verdict)
        if kind is ExpectationKind.VENUE:
            if verdict is Verdict.YES:
                return CaseGrade(False, "said yes where the venue decides", verdict)
            if not any(m in normalized for m in self._contact_markers):
                return CaseGrade(False, "did not send the customer to the venue", verdict)
        for group in case.must:
            if not any(GradingText.normalize(alternative) in normalized for alternative in group):
                return CaseGrade(False, f"missing «{group[0]}»", verdict)
        return CaseGrade(True, "ok", verdict)
