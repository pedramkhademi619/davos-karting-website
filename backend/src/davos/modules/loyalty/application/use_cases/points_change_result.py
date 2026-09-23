from dataclasses import dataclass


@dataclass(frozen=True)
class PointsChangeResult:
    balance: int
    applied: bool  # False when this source event had already been processed
