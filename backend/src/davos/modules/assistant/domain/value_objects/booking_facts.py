from __future__ import annotations

from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class BookingFacts:
    """The booking facts in force right now, as the assistant needs them.

    Kart counts, prices, closed days, the session grid and the hold time are the owner's
    admin-panel settings; the composition root (ScheduleBookingFacts) reads them live. None of them is written in code
    or in a knowledge file, where they would go stale.
    """

    singles_per_session: int
    doubles_per_session: int
    normal_single_toman: int
    normal_double_toman: int
    holiday_single_toman: int
    holiday_double_toman: int
    holiday_weekdays: frozenset[int]  # Python weekday numbers (Monday = 0)
    closed_weekdays: frozenset[int]
    online_booking_enabled: bool
    min_days_ahead: int
    hold_minutes: int
    first_session: time  # the evening shift
    interval_minutes: int
    last_session_before: time | None = None  # end of the evening shift (after midnight when not after the start)
    morning_shift: tuple[time, time] | None = None  # (first session, end) when there is a morning shift
    # When under-15s may ride: weekdays (Monday = 0), from (inclusive) and until (exclusive), and whether the window
    # binds every under-15 (True) or only 11-14 year olds driving a single-seater (False).
    junior_weekdays: frozenset[int] | None = None
    junior_from: time | None = None
    junior_until: time | None = None
    junior_everyone: bool = False
