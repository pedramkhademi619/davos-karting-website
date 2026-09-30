from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookingFacts:
    """The booking facts in force right now, as the assistant needs them.

    Kart counts, prices, closed days and the hold time are the owner's admin-panel settings, and the phone number is
    the deployment's CONTACT_PHONE; the composition root (ScheduleBookingFacts) reads them live. None of them is
    written in code or in a knowledge file, where they would go stale.
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
    contact_phone: str  # blank when not configured: then no phone number is quoted
