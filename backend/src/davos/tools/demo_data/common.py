"""Small helpers shared by the demo-data generators: time, ids and random choices (everything is seeded)."""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")
RIAL_PER_TOMAN = 10
MARK = "DM"  # demo reservations carry codes "DM-XXXXXXXX"; demo rows elsewhere are recognised by their own fields


def at(day: date, clock: time) -> datetime:
    """A Tehran wall-clock moment on a calendar day."""
    return datetime.combine(day, clock, tzinfo=TEHRAN)


def random_clock(rng: random.Random, start_hour: int, end_hour: int) -> time:
    return time(rng.randint(start_hour, end_hour - 1), rng.randint(0, 59), rng.randint(0, 59))


MARK_TAIL = 0xD3A0D3A0D3A0  # every demo uuid ends in these 48 bits, so demo rows can be found (and removed) later
MARK_SUFFIX = "-d3a0d3a0d3a0"


def new_id(rng: random.Random) -> uuid.UUID:
    value = (rng.getrandbits(80) << 48) | MARK_TAIL
    value = (value & ~(0xF << 76)) | (0x4 << 76)  # version 4
    value = (value & ~(0x3 << 62)) | (0x2 << 62)  # RFC 4122 variant
    return uuid.UUID(int=value)


def session_times() -> list[time]:
    """The sellable sessions of a day: every 10 minutes from 15:00 to 01:00, never the :50 refuelling slot."""
    result: list[time] = []
    for minutes in range(0, 600, 10):
        moment = (15 * 60 + minutes) % 1440
        if moment % 60 != 50:
            result.append(time(moment // 60, moment % 60))
    return result


def starts_at(day: date, session: time) -> datetime:
    """Sessions after midnight belong to the same business day but start on the next calendar day."""
    return at(day + timedelta(days=1) if session < time(15, 0) else day, session)


def chunks[T](items: list[T], size: int) -> list[list[T]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def weighted[T](rng: random.Random, pairs: list[tuple[T, float]]) -> T:
    return rng.choices([p[0] for p in pairs], weights=[p[1] for p in pairs], k=1)[0]
