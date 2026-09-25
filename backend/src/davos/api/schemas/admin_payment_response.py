from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt


class AdminPaymentResponse(BaseModel):
    payment_id: uuid.UUID
    order_ref: str
    customer_id: uuid.UUID
    amount_toman: int
    status: str
    gateway: str
    gateway_order_id: int | None
    reference_id: str | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    settled_at: datetime | None

    @classmethod
    def of(cls, p: PaymentAttempt) -> AdminPaymentResponse:
        return cls(
            payment_id=p.id,
            order_ref=p.order_ref,
            customer_id=p.customer_id,
            amount_toman=p.amount.irr // 10,
            status=p.status.value,
            gateway=p.gateway,
            gateway_order_id=p.gateway_order_id,
            reference_id=p.reference_id,
            failure_reason=p.failure_reason,
            created_at=p.created_at,
            updated_at=p.updated_at,
            settled_at=p.settled_at,
        )
