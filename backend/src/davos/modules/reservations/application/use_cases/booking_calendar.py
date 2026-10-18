from __future__ import annotations

from dataclasses import dataclass

from davos.modules.reservations.application.use_cases.bookable_day import BookableDay


@dataclass(frozen=True)
class BookingCalendar:
    online_booking_enabled: bool
    days: list[BookableDay]
    hold_minutes: int
    max_karts_per_reservation: int
