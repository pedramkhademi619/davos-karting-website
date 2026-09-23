from __future__ import annotations

import uuid

from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.modules.payments.domain.errors.payment_not_found_error import PaymentNotFoundError
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class GetPaymentStatusUseCase:
    """A customer can see only their own payments; foreign ids answer exactly like missing ones."""

    def __init__(self, *, uow: UnitOfWork, payments: PaymentRepository) -> None:
        self._uow = uow
        self._payments = payments

    async def execute(self, *, payment_id: uuid.UUID, customer_id: uuid.UUID) -> PaymentAttempt:
        async with self._uow:
            payment = await self._payments.get_owned(payment_id, customer_id)
        if payment is None:
            raise PaymentNotFoundError
        return payment
