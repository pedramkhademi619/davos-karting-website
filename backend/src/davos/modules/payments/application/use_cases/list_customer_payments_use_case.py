from __future__ import annotations

import uuid

from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class ListCustomerPaymentsUseCase:
    """The signed-in customer's own payment attempts, newest first, for their account page."""

    def __init__(self, *, uow: UnitOfWork, payments: PaymentRepository) -> None:
        self._uow = uow
        self._payments = payments

    async def execute(self, customer_id: uuid.UUID, *, limit: int = 100) -> list[PaymentAttempt]:
        async with self._uow:
            return await self._payments.list_for_customer(customer_id, limit=limit)
