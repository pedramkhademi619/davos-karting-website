from __future__ import annotations

from datetime import date, datetime, time, timedelta

from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.modules.reservations.domain.value_objects.tehran_time import TEHRAN, business_date


class SessionCalendar:
    """Which days and session times exist, and which of them can be booked right now.

    A business day runs from ``shift_start`` to ``shift_end``; when the end is at or before the start the shift runs
    past midnight, and a 00:30 session belongs to the business day that started the evening before.
    """

    def __init__(self, settings: ScheduleSettings) -> None:
        self._settings = settings

    def session_times(self) -> list[time]:
        start = self._minutes(self._settings.shift_start)
        end = self._minutes(self._settings.shift_end)
        if end <= start:
            end += 24 * 60
        return [time((m // 60) % 24, m % 60) for m in range(start, end, self._settings.interval_minutes)]

    def is_session_time(self, value: time) -> bool:
        return value in set(self.session_times())

    def starts_at(self, day: date, value: time) -> datetime:
        calendar_day = day + timedelta(days=1) if value < self._settings.shift_start else day
        return datetime.combine(calendar_day, value, tzinfo=TEHRAN)

    def bookable_dates(self, now: datetime) -> list[date]:
        today = business_date(now)
        offsets = range(self._settings.min_days_ahead, self._settings.max_days_ahead + 1)
        days = [today + timedelta(days=offset) for offset in offsets]
        return [d for d in days if not self._settings.is_closed(d)]

    def is_bookable(self, day: date, value: time, now: datetime) -> bool:
        if not self._settings.online_booking_enabled or day not in self.bookable_dates(now):
            return False
        if not self.is_session_time(value):
            return False
        earliest = now + timedelta(minutes=self._settings.same_day_lead_minutes)
        return self.starts_at(day, value) >= earliest

    @staticmethod
    def _minutes(value: time) -> int:
        return value.hour * 60 + value.minute
