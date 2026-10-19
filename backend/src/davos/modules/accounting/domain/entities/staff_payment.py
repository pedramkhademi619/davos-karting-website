from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime

PAYMENT_KINDS = {"salary": "حقوق", "advance": "مساعده", "bonus": "پاداش"}


@dataclass(frozen=True)
class StaffPayment:
    """Money handed to a staff member. Salary and advance count against the month's salary; a bonus is on top."""

    payment_id: uuid.UUID
    staff_id: uuid.UUID
    kind: str  # one of PAYMENT_KINDS
    amount_irr: int
    month_key: str  # Jalali "1405-07": the month this payment is for
    paid_on: date
    note: str
    entry_id: uuid.UUID | None  # the journal entry that booked it as a payroll expense
    created_by: str
    created_at: datetime
