from __future__ import annotations

from dataclasses import dataclass
from datetime import date

_MONTHS = (
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
)
_WEEKDAYS = ("دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه")  # Python weekday order
_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_CUMULATIVE_DAYS = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


@dataclass(frozen=True)
class JalaliDate:
    """A date on the Iranian (Solar Hijri) calendar, for texts shown to customers (SMS, tickets)."""

    year: int
    month: int
    day: int
    weekday_name: str

    @classmethod
    def from_gregorian(cls, value: date) -> JalaliDate:
        gy, gm, gd = value.year, value.month, value.day
        gy2 = gy + 1 if gm > 2 else gy
        days = (
            355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 + gd + _CUMULATIVE_DAYS[gm - 1]
        )
        jy = -1595 + 33 * (days // 12053)
        days %= 12053
        jy += 4 * (days // 1461)
        days %= 1461
        if days > 365:
            jy += (days - 1) // 365
            days = (days - 1) % 365
        if days < 186:
            jm, jd = 1 + days // 31, 1 + days % 31
        else:
            jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
        return cls(jy, jm, jd, _WEEKDAYS[value.weekday()])

    @property
    def month_name(self) -> str:
        return _MONTHS[self.month - 1]

    def numeric(self, *, persian_digits: bool = True) -> str:
        text = f"{self.year:04d}/{self.month:02d}/{self.day:02d}"
        return text.translate(_PERSIAN_DIGITS) if persian_digits else text

    def long(self) -> str:
        return f"{self.day} {self.month_name} {self.year}".translate(_PERSIAN_DIGITS)
