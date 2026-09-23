from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.modules.payments.domain.enums.payment_status import PaymentStatus


class InMemoryPaymentRepository(PaymentRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, PaymentAttempt] = {}

    async def add(self, payment: PaymentAttempt) -> None:
        self.items[payment.id] = payment

    async def get_for_update(self, payment_id: uuid.UUID) -> PaymentAttempt | None:
        return self.items.get(payment_id)

    async def get_by_authority_for_update(self, authority: str) -> PaymentAttempt | None:
        return next((p for p in self.items.values() if p.authority == authority), None)

    async def get_owned(self, payment_id: uuid.UUID, customer_id: uuid.UUID) -> PaymentAttempt | None:
        payment = self.items.get(payment_id)
        return payment if payment and payment.customer_id == customer_id else None

    async def has_paid_for_order(self, order_ref: str) -> bool:
        return any(p.order_ref == order_ref and p.status is PaymentStatus.PAID for p in self.items.values())

    async def save(self, payment: PaymentAttempt) -> None:
        self.items[payment.id] = payment

    async def list_reconcilable(self, *, now: datetime, stuck_for_seconds: int, limit: int) -> list[uuid.UUID]:
        stuck_before = now - timedelta(seconds=stuck_for_seconds)
        ids = [
            p.id
            for p in self.items.values()
            if (p.status in {PaymentStatus.UNKNOWN, PaymentStatus.VERIFYING} and p.updated_at <= stuck_before)
            or (p.status in {PaymentStatus.CREATED, PaymentStatus.REDIRECTED} and p.expires_at <= now)
        ]
        return ids[:limit]
