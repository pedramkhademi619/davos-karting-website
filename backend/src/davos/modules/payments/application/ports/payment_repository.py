from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.payments.application.ports.payment_page import PaymentPage
from davos.modules.payments.application.ports.payment_query import PaymentQuery
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt


class PaymentRepository(ABC):
    @abstractmethod
    async def add(self, payment: PaymentAttempt) -> None: ...

    @abstractmethod
    async def next_gateway_order_id(self) -> int:
        """A new, never reused numeric order id for the bank (database sequence)."""

    @abstractmethod
    async def get_for_update(self, payment_id: uuid.UUID) -> PaymentAttempt | None: ...

    @abstractmethod
    async def get_by_authority_for_update(self, authority: str) -> PaymentAttempt | None: ...

    @abstractmethod
    async def get_owned(self, payment_id: uuid.UUID, customer_id: uuid.UUID) -> PaymentAttempt | None: ...

    @abstractmethod
    async def lock_order(self, order_ref: str) -> None:
        """Serialise the "is this order already paid?" decision for one order until the transaction ends."""

    @abstractmethod
    async def has_paid_for_order(self, order_ref: str, *, excluding: uuid.UUID | None = None) -> bool: ...

    @abstractmethod
    async def save(self, payment: PaymentAttempt) -> None: ...

    @abstractmethod
    async def search(self, query: PaymentQuery) -> PaymentPage: ...

    @abstractmethod
    async def list_reconcilable(self, *, now: datetime, stuck_for_seconds: int, limit: int) -> list[uuid.UUID]:
        """Ids of attempts that are UNKNOWN, stuck VERIFYING, paid but unsettled, waiting for a refund, or overdue
        and still open."""
