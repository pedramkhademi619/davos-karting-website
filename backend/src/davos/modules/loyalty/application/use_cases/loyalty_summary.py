from dataclasses import dataclass


@dataclass(frozen=True)
class LoyaltySummary:
    balance: int
    lifetime_points: int
    tier_name: str
    next_tier_name: str | None
    points_to_next_tier: int | None
    expiring_soon: int
