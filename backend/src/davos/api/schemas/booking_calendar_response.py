from __future__ import annotations

from pydantic import BaseModel

from davos.api.schemas.bookable_day_response import BookableDayResponse


class BookingCalendarResponse(BaseModel):
    online_booking_enabled: bool
    payments_enabled: bool
    hold_minutes: int
    max_karts_per_reservation: int
    days: list[BookableDayResponse]
