from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from davos.modules.reservations.domain.value_objects.price_tier import PriceTier


@dataclass(frozen=True)
class BookableDay:
    day: date
    is_holiday: bool
    prices: PriceTier
