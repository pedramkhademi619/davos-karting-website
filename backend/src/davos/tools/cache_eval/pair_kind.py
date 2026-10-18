from enum import StrEnum


class PairKind(StrEnum):
    SAME = "same"  # two ways of asking one question: the stored answer of one is right for the other
    DIFFERENT = "different"  # similar wording, different answer: one must never be served for the other
    UNCACHEABLE = "uncacheable"  # each is a question the cache must stay out of (age, day, hour, follow-up, ...)
