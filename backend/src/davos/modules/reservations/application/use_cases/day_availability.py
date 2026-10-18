from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from davos.modules.reservations.application.use_cases.session_availability import SessionAvailability
from davos.modules.reservations.domain.value_objects.price_tier import PriceTier


@dataclass(frozen=True)
class DayAvailability:
    day: date
    is_holiday: bool
    is_closed: bool
    prices: PriceTier
    sessions: list[SessionAvailability]
