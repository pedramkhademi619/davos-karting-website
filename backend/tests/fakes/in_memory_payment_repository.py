from __future__ import annotations

import itertools
import uuid
from datetime import datetime, timedelta

from davos.modules.payments.application.ports.payment_page import PaymentPage
from davos.modules.payments.application.ports.payment_query import PaymentQuery
from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.modules.payments.domain.enums.payment_status import PaymentStatus


class InMemoryPaymentRepository(PaymentRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, PaymentAttempt] = {}
        self._order_ids = itertools.count(1_000_001)
        self.locked_orders: list[str] = []

    async def add(self, payment: PaymentAttempt) -> None:
        self.items[payment.id] = payment

    async def next_gateway_order_id(self) -> int:
        return next(self._order_ids)

    async def get_for_update(self, payment_id: uuid.UUID) -> PaymentAttempt | None:
        return self.items.get(payment_id)

    async def get_by_authority_for_update(self, authority: str) -> PaymentAttempt | None:
        return next((p for p in self.items.values() if p.authority == authority), None)

    async def get_owned(self, payment_id: uuid.UUID, customer_id: uuid.UUID) -> PaymentAttempt | None:
        payment = self.items.get(payment_id)
        return payment if payment and payment.customer_id == customer_id else None

    async def lock_order(self, order_ref: str) -> None:
        self.locked_orders.append(order_ref)

    async def has_paid_for_order(self, order_ref: str, *, excluding: uuid.UUID | None = None) -> bool:
        return any(
            p.order_ref == order_ref and p.status is PaymentStatus.PAID and p.id != excluding
            for p in self.items.values()
        )

    async def save(self, payment: PaymentAttempt) -> None:
        self.items[payment.id] = payment

    async def search(self, query: PaymentQuery) -> PaymentPage:
        items = sorted(self.items.values(), key=lambda p: p.created_at, reverse=True)
        if query.status is not None:
            items = [p for p in items if p.status is query.status]
        paid = sum(p.amount.irr for p in items if p.status is PaymentStatus.PAID)
        return PaymentPage(
            items=items[query.offset : query.offset + query.limit], total=len(items), paid_total_irr=paid
        )

    async def list_reconcilable(self, *, now: datetime, stuck_for_seconds: int, limit: int) -> list[uuid.UUID]:
        stuck_before = now - timedelta(seconds=stuck_for_seconds)
        ids = [
            p.id
            for p in self.items.values()
            if (p.status in {PaymentStatus.UNKNOWN, PaymentStatus.VERIFYING} and p.updated_at <= stuck_before)
            or (p.needs_settlement and p.updated_at <= stuck_before)
            or p.status is PaymentStatus.REFUND_PENDING
            or (p.status in {PaymentStatus.CREATED, PaymentStatus.REDIRECTED} and p.expires_at <= now)
        ]
        return ids[:limit]
