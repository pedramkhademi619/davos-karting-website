from dataclasses import dataclass


@dataclass(frozen=True)
class TierRule:
    name: str
    min_lifetime_points: int
