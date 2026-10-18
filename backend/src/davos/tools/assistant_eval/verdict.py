from enum import StrEnum


class Verdict(StrEnum):
    """What a reply's opening says, as read by VerdictClassifier."""

    YES = "yes"
    NO = "no"
    UNCLEAR = "unclear"
