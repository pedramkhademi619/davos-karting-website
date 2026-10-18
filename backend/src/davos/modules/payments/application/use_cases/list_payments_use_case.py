from __future__ import annotations

from davos.modules.payments.application.ports.payment_page import PaymentPage
from davos.modules.payments.application.ports.payment_query import PaymentQuery
from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class ListPaymentsUseCase:
    """All payment attempts, newest first, for the admin panel."""

    def __init__(self, *, uow: UnitOfWork, payments: PaymentRepository) -> None:
        self._uow = uow
        self._payments = payments

    async def execute(self, query: PaymentQuery) -> PaymentPage:
        async with self._uow:
            return await self._payments.search(query)
