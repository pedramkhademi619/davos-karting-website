from __future__ import annotations

import uuid
from datetime import date as Date  # noqa: N812 - a field is called date
from datetime import datetime

from pydantic import BaseModel

from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.value_objects.tehran_time import local
from davos.shared_kernel.domain.jalali_date import JalaliDate


class ReservationResponse(BaseModel):
    id: uuid.UUID
    code: str
    date: Date
    date_jalali: str
    weekday: str
    time: str
    starts_at: datetime
    single_count: int
    double_count: int
    people: int
    amount_toman: int
    status: str
    source: str
    contact_name: str
    contact_mobile: str
    hold_expires_at: datetime | None
    confirmed_at: datetime | None
    created_at: datetime
    confirmed_late: bool
    note: str = ""
    cancel_reason: str = ""

    @classmethod
    def of(cls, reservation: Reservation, *, staff_view: bool = False) -> ReservationResponse:
        day = JalaliDate.from_gregorian(reservation.business_date)
        return cls(
            id=reservation.id,
            code=reservation.code,
            date=reservation.business_date,
            date_jalali=day.numeric(persian_digits=False),
            weekday=day.weekday_name,
            time=local(reservation.starts_at).strftime("%H:%M"),
            starts_at=reservation.starts_at,
            single_count=reservation.single_count,
            double_count=reservation.double_count,
            people=reservation.people,
            amount_toman=reservation.amount.irr // 10,
            status=reservation.status.value,
            source=reservation.source.value,
            contact_name=reservation.contact_name,
            contact_mobile=reservation.contact_mobile,
            hold_expires_at=reservation.hold_expires_at,
            confirmed_at=reservation.confirmed_at,
            created_at=reservation.created_at,
            confirmed_late=reservation.confirmed_late,
            note=reservation.note if staff_view else "",
            cancel_reason=reservation.cancel_reason,
        )
