from __future__ import annotations

from datetime import date, timedelta

from davos.shared_kernel.domain.jalali_date import JalaliDate


class FiscalCalendar:
    """The Iranian fiscal year is the Jalali year (1 Farvardin to the end of Esfand); months are Jalali months."""

    @staticmethod
    def year_of(day: date) -> int:
        return JalaliDate.from_gregorian(day).year

    @staticmethod
    def month_of(day: date) -> tuple[int, int]:
        jalali = JalaliDate.from_gregorian(day)
        return jalali.year, jalali.month

    @staticmethod
    def month_key(year: int, month: int) -> str:
        return f"{year:04d}-{month:02d}"

    @staticmethod
    def year_start(year: int) -> date:
        probe = date(year + 621, 3, 18)
        for offset in range(7):
            candidate = probe + timedelta(days=offset)
            jalali = JalaliDate.from_gregorian(candidate)
            if (jalali.year, jalali.month, jalali.day) == (year, 1, 1):
                return candidate
        raise ValueError(f"cannot place 1 Farvardin {year}")

    @classmethod
    def year_end(cls, year: int) -> date:
        return cls.year_start(year + 1) - timedelta(days=1)

    @classmethod
    def month_start(cls, year: int, month: int) -> date:
        before = 31 * min(month - 1, 6) + 30 * max(month - 7, 0)
        return cls.year_start(year) + timedelta(days=before)

    @classmethod
    def month_end(cls, year: int, month: int) -> date:
        if month == 12:
            return cls.year_end(year)
        return cls.month_start(year, month + 1) - timedelta(days=1)
