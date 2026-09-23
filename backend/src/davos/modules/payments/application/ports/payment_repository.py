from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt


class PaymentRepository(ABC):
    @abstractmethod
    async def add(self, payment: PaymentAttempt) -> None: ...

    @abstractmethod
    async def get_for_update(self, payment_id: uuid.UUID) -> PaymentAttempt | None: ...

    @abstractmethod
    async def get_by_authority_for_update(self, authority: str) -> PaymentAttempt | None: ...

    @abstractmethod
    async def get_owned(self, payment_id: uuid.UUID, customer_id: uuid.UUID) -> PaymentAttempt | None: ...

    @abstractmethod
    async def has_paid_for_order(self, order_ref: str) -> bool: ...

    @abstractmethod
    async def save(self, payment: PaymentAttempt) -> None: ...

    @abstractmethod
    async def list_reconcilable(self, *, now: datetime, stuck_for_seconds: int, limit: int) -> list[uuid.UUID]:
        """Ids of attempts that are UNKNOWN, stuck VERIFYING, or overdue and still open."""
