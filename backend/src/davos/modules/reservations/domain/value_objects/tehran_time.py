"""Local time of the track. Iran has used a fixed UTC+03:30 offset since daylight saving was abolished in 2022."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

TEHRAN = timezone(timedelta(hours=3, minutes=30), name="Asia/Tehran")

# Before this hour the previous business day is still running (the shift ends after midnight).
BUSINESS_DAY_ROLLOVER_HOUR = 6


def local(moment: datetime) -> datetime:
    return moment.astimezone(TEHRAN)


def business_date(moment: datetime) -> date:
    """The working day a moment belongs to: 00:30 on Sunday is still Saturday's shift."""
    here = local(moment)
    if here.hour < BUSINESS_DAY_ROLLOVER_HOUR:
        return here.date() - timedelta(days=1)
    return here.date()
