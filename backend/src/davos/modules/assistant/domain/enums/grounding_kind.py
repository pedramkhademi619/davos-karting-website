from enum import StrEnum


class GroundingKind(StrEnum):
    GROUNDED = "grounded"
    NO_ANSWER = "no_answer"
    UNGROUNDED = "ungrounded"
    LEAK = "leak"
