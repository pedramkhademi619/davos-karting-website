from __future__ import annotations

from datetime import date as Date  # noqa: N812 - a field is called date

from pydantic import BaseModel

from davos.modules.reservations.application.use_cases.bookable_day import BookableDay
from davos.shared_kernel.domain.jalali_date import JalaliDate


class BookableDayResponse(BaseModel):
    date: Date
    date_jalali: str
    weekday: str
    is_holiday: bool
    single_price_toman: int
    double_price_toman: int

    @classmethod
    def of(cls, day: BookableDay) -> BookableDayResponse:
        jalali = JalaliDate.from_gregorian(day.day)
        return cls(
            date=day.day,
            date_jalali=jalali.numeric(persian_digits=False),
            weekday=jalali.weekday_name,
            is_holiday=day.is_holiday,
            single_price_toman=day.prices.single.irr // 10,
            double_price_toman=day.prices.double.irr // 10,
        )
