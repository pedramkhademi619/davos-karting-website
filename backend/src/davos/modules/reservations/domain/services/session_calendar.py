from __future__ import annotations

from datetime import date, datetime, time, timedelta

from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.modules.reservations.domain.value_objects.tehran_time import TEHRAN, business_date, local


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

    def is_blocked(self, value: time) -> bool:
        """A session time on the grid that is never sold, online or at the counter (the karts are refuelled then)."""
        return value.minute in self._settings.blocked_minutes

    def is_sellable_time(self, value: time) -> bool:
        return self.is_session_time(value) and not self.is_blocked(value)

    def starts_at(self, day: date, value: time) -> datetime:
        calendar_day = day + timedelta(days=1) if value < self._settings.shift_start else day
        return datetime.combine(calendar_day, value, tzinfo=TEHRAN)

    def bookable_dates(self, now: datetime) -> list[date]:
        today = business_date(now)
        offsets = range(self._settings.min_days_ahead, self._settings.max_days_ahead + 1)
        days = [today + timedelta(days=offset) for offset in offsets]
        return [d for d in days if not self._settings.is_closed(d)]

    def is_online_cutoff_passed(self, now: datetime) -> bool:
        """Past this time of day (any date), online booking is refused -- the customer must come in person."""
        cutoff = self._settings.online_booking_cutoff
        return cutoff is not None and local(now).time() >= cutoff

    def is_bookable(self, day: date, value: time, now: datetime) -> bool:
        if not self._settings.online_booking_enabled or day not in self.bookable_dates(now):
            return False
        if not self.is_sellable_time(value) or self.is_online_cutoff_passed(now):
            return False
        earliest = now + timedelta(minutes=self._settings.same_day_lead_minutes)
        return self.starts_at(day, value) >= earliest

    @staticmethod
    def _minutes(value: time) -> int:
        return value.hour * 60 + value.minute
