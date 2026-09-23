from enum import StrEnum


class AnswerOutcome(StrEnum):
    ANSWERED = "answered"
    SMALL_TALK = "small_talk"
    QUICK_ANSWER = "quick_answer"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    REFUSED_UNSAFE_INPUT = "refused_unsafe_input"
    FALLBACK_PROVIDER_UNAVAILABLE = "fallback_provider_unavailable"
    FALLBACK_BUDGET_EXHAUSTED = "fallback_budget_exhausted"
