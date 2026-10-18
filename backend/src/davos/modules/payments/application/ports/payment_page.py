from __future__ import annotations

from dataclasses import dataclass

from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt


@dataclass(frozen=True)
class PaymentPage:
    items: list[PaymentAttempt]
    total: int
    paid_total_irr: int
