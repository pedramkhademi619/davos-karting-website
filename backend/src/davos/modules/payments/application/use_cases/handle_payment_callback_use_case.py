from __future__ import annotations

from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.application.services.payment_settlement_service import PaymentSettlementService
from davos.modules.payments.application.use_cases.payment_callback_command import PaymentCallbackCommand
from davos.modules.payments.application.use_cases.payment_callback_result import PaymentCallbackResult
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.modules.payments.domain.errors.payment_not_found_error import PaymentNotFoundError
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class HandlePaymentCallbackUseCase:
    """The browser callback only *triggers* verification; the result comes from the provider."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        payments: PaymentRepository,
        settlement: PaymentSettlementService,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._payments = payments
        self._settlement = settlement
        self._clock = clock

    async def execute(self, command: PaymentCallbackCommand) -> PaymentCallbackResult:
        async with self._uow:
            payment = await self._payments.get_by_authority_for_update(command.authority)
            if payment is None or payment.customer_id != command.customer_id:
                raise PaymentNotFoundError
            payment_id = payment.id

            if command.status_param.upper() != "OK" and payment.status is PaymentStatus.REDIRECTED:
                payment.mark_failed("cancelled_by_customer", self._clock.now())
                await self._payments.save(payment)
                self._uow.collect_events(payment.pull_events())
                await self._uow.commit()
                return PaymentCallbackResult(payment_id, payment.status)

        # "Status=OK" in a URL proves nothing: always verify with the provider.
        status = await self._settlement.settle(payment_id)
        return PaymentCallbackResult(payment_id, status)
