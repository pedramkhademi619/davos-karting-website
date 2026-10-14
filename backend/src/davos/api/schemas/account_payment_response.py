from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.modules.payments.domain.enums.payment_status import PaymentStatus


class AccountPaymentResponse(BaseModel):
    payment_id: uuid.UUID
    status: str
    amount_toman: int
    reference_id: str | None = None
    reservation_id: uuid.UUID | None = None
    gateway: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, payment: PaymentAttempt, *, reservation_id: uuid.UUID | None) -> AccountPaymentResponse:
        return cls(
            payment_id=payment.id,
            status=payment.status.value,
            amount_toman=payment.amount.irr // 10,  # display conversion; Rial stays the stored base unit
            reference_id=payment.reference_id if payment.status is PaymentStatus.PAID else None,
            reservation_id=reservation_id,
            gateway=payment.gateway,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
