from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class StaffReservationCommand:
    day: date
    session_time: time
    single_count: int
    double_count: int
    contact_name: str
    contact_mobile: str
    note: str
    amount_irr: int
    allow_overbooking: bool = False
