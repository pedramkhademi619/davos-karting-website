from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from davos.modules.reservations.domain.services.session_calendar import SessionCalendar
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings

# Python weekday numbers (Monday = 0) in the order of the Iranian week, which starts on Saturday.
_WEEK_ORDER = (5, 6, 0, 1, 2, 3, 4)
_WEEKDAY_NAMES = {5: "شنبه", 6: "یکشنبه", 0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه", 3: "پنجشنبه", 4: "جمعه"}


def _names(days: frozenset[int]) -> list[str]:
    return [_WEEKDAY_NAMES[d] for d in _WEEK_ORDER if d in days]


class BookingInfoResponse(BaseModel):
    """Public facts the website shows (home, FAQ, booking page); all of them are edited in the admin panel."""

    online_booking_enabled: bool
    payments_enabled: bool
    single_capacity: int
    double_capacity: int
    normal_single_toman: int
    normal_double_toman: int
    holiday_single_toman: int
    holiday_double_toman: int
    holiday_weekdays: list[str]
    closed_weekdays: list[str]
    first_session: str  # the evening shift
    last_session_before: str
    morning_shift_enabled: bool
    morning_first_session: str
    morning_last_session_before: str
    interval_minutes: int
    hold_minutes: int
    min_days_ahead: int
    max_days_ahead: int
    max_karts_per_reservation: int
    daily_booking_limit_mode: str
    daily_people_limit: int | None
    daily_ticket_limit: int | None
    online_booking_cutoff: str | None
    online_booking_cutoff_passed: bool
    # When under-15s may ride (the booking wizard applies it; weekday names as in the calendar).
    junior_weekdays: list[str]
    junior_from: str
    junior_until: str
    junior_scope: str

    @classmethod
    def of(cls, s: ScheduleSettings, *, payments_enabled: bool, now: datetime) -> BookingInfoResponse:
        return cls(
            online_booking_enabled=s.online_booking_enabled,
            payments_enabled=payments_enabled,
            single_capacity=s.single_capacity,
            double_capacity=s.double_capacity,
            normal_single_toman=s.normal_prices.single.to_toman(),
            normal_double_toman=s.normal_prices.double.to_toman(),
            holiday_single_toman=s.holiday_prices.single.to_toman(),
            holiday_double_toman=s.holiday_prices.double.to_toman(),
            holiday_weekdays=_names(s.holiday_weekdays),
            closed_weekdays=_names(s.closed_weekdays),
            first_session=s.shift_start.strftime("%H:%M"),
            last_session_before=s.shift_end.strftime("%H:%M"),
            morning_shift_enabled=s.morning_shift_enabled,
            morning_first_session=s.morning_start.strftime("%H:%M"),
            morning_last_session_before=s.morning_end.strftime("%H:%M"),
            interval_minutes=s.interval_minutes,
            hold_minutes=s.hold_minutes,
            min_days_ahead=s.min_days_ahead,
            max_days_ahead=s.max_days_ahead,
            max_karts_per_reservation=s.max_karts_per_reservation,
            daily_booking_limit_mode=s.daily_booking_limit_mode.value,
            daily_people_limit=s.daily_people_limit,
            daily_ticket_limit=s.daily_ticket_limit,
            online_booking_cutoff=s.online_booking_cutoff.strftime("%H:%M") if s.online_booking_cutoff else None,
            online_booking_cutoff_passed=SessionCalendar(s).is_online_cutoff_passed(now),
            junior_weekdays=_names(s.junior_weekdays),
            junior_from=s.junior_from.strftime("%H:%M"),
            junior_until=s.junior_until.strftime("%H:%M"),
            junior_scope=s.junior_scope.value,
        )
