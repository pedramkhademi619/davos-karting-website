from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class HoldReservationCommand:
    customer_id: uuid.UUID
    day: date
    session_time: time
    single_count: int
    double_count: int
    contact_name: str
    contact_mobile: str
