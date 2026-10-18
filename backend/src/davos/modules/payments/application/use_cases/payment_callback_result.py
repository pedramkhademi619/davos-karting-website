import uuid
from dataclasses import dataclass

from davos.modules.payments.domain.enums.payment_status import PaymentStatus


@dataclass(frozen=True)
class PaymentCallbackResult:
    payment_id: uuid.UUID
    status: PaymentStatus
    order_ref: str = ""
