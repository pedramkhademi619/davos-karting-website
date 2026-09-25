from __future__ import annotations

from datetime import date as Date  # noqa: N812 - a field is called date

from pydantic import BaseModel

from davos.api.schemas.session_availability_response import SessionAvailabilityResponse
from davos.modules.reservations.application.use_cases.day_availability import DayAvailability
from davos.modules.reservations.domain.value_objects.tehran_time import local
from davos.shared_kernel.domain.jalali_date import JalaliDate


class DayAvailabilityResponse(BaseModel):
    date: Date
    date_jalali: str
    weekday: str
    is_holiday: bool
    is_closed: bool
    single_price_toman: int
    double_price_toman: int
    sessions: list[SessionAvailabilityResponse]

    @classmethod
    def of(cls, day: DayAvailability) -> DayAvailabilityResponse:
        jalali = JalaliDate.from_gregorian(day.day)
        return cls(
            date=day.day,
            date_jalali=jalali.numeric(persian_digits=False),
            weekday=jalali.weekday_name,
            is_holiday=day.is_holiday,
            is_closed=day.is_closed,
            single_price_toman=day.prices.single.irr // 10,
            double_price_toman=day.prices.double.irr // 10,
            sessions=[
                SessionAvailabilityResponse(
                    time=local(s.starts_at).strftime("%H:%M"),
                    starts_at=s.starts_at,
                    singles_left=s.singles_left,
                    doubles_left=s.doubles_left,
                    single_capacity=s.single_capacity,
                    double_capacity=s.double_capacity,
                    bookable=s.bookable,
                )
                for s in day.sessions
            ],
        )
