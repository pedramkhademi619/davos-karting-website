from __future__ import annotations

from pydantic import BaseModel

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
    first_session: str
    last_session_before: str
    interval_minutes: int
    hold_minutes: int
    min_days_ahead: int
    max_days_ahead: int
    max_karts_per_reservation: int

    @classmethod
    def of(cls, s: ScheduleSettings, *, payments_enabled: bool) -> BookingInfoResponse:
        return cls(
            online_booking_enabled=s.online_booking_enabled,
            payments_enabled=payments_enabled,
            single_capacity=s.single_capacity,
            double_capacity=s.double_capacity,
            normal_single_toman=s.normal_prices.single.irr // 10,
            normal_double_toman=s.normal_prices.double.irr // 10,
            holiday_single_toman=s.holiday_prices.single.irr // 10,
            holiday_double_toman=s.holiday_prices.double.irr // 10,
            holiday_weekdays=_names(s.holiday_weekdays),
            closed_weekdays=_names(s.closed_weekdays),
            first_session=s.shift_start.strftime("%H:%M"),
            last_session_before=s.shift_end.strftime("%H:%M"),
            interval_minutes=s.interval_minutes,
            hold_minutes=s.hold_minutes,
            min_days_ahead=s.min_days_ahead,
            max_days_ahead=s.max_days_ahead,
            max_karts_per_reservation=s.max_karts_per_reservation,
        )
