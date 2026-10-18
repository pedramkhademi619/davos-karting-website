from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

_TEHRAN = ZoneInfo("Asia/Tehran")


class TehranCalendar:
    @staticmethod
    def today(now: datetime) -> date:
        return now.astimezone(_TEHRAN).date()
