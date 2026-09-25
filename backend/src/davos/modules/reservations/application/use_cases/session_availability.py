from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time


@dataclass(frozen=True)
class SessionAvailability:
    session_time: time
    starts_at: datetime
    singles_left: int
    doubles_left: int
    single_capacity: int
    double_capacity: int
    bookable: bool
