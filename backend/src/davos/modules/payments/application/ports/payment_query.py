from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from davos.modules.payments.domain.enums.payment_status import PaymentStatus


@dataclass(frozen=True)
class PaymentQuery:
    status: PaymentStatus | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    text: str = ""  # order reference, bank reference or authority
    offset: int = 0
    limit: int = 50
