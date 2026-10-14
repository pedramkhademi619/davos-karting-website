from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

from davos.modules.reservations.domain.enums.counter_payment_method import CounterPaymentMethod


@dataclass(frozen=True)
class StaffReservationCommand:
    day: date
    session_time: time
    single_count: int
    double_count: int
    contact_name: str
    contact_mobile: str
    note: str
    amount_irr: int
    allow_overbooking: bool = False
    payment_method: CounterPaymentMethod = CounterPaymentMethod.NONE
