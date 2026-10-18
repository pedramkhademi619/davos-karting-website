from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReservationStats:
    confirmed: int
    attended: int
    cancelled: int
    held: int
    karts: int
    people: int
    online_revenue_irr: int
