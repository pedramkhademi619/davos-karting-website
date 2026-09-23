from enum import StrEnum


class PointsEntryKind(StrEnum):
    EARN = "earn"
    SPEND = "spend"
    EXPIRE = "expire"
    ADJUST = "adjust"
    REVERSAL = "reversal"
