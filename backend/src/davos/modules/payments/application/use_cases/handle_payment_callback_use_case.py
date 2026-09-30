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
    """The browser callback only *triggers* verification; the result comes from the bank.

    The attempt is found by the gateway token and, when the gateway reports one, must also match our numeric order
    id, so a callback cannot be pointed at another customer's attempt. A "not paid" callback only fails an attempt that
    the bank has never reported back on.
    """

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
            if payment is None:
                raise PaymentNotFoundError
            if command.customer_id is not None and payment.customer_id != command.customer_id:
                raise PaymentNotFoundError
            if command.gateway_order_id is not None and payment.gateway_order_id != command.gateway_order_id:
                raise PaymentNotFoundError
            payment_id, order_ref = payment.id, payment.order_ref

            if not command.succeeded:
                if payment.status is PaymentStatus.REDIRECTED and payment.provider_reference is None:
                    code = (command.provider_code or "").strip()[:20]
                    payment.mark_failed(f"gateway_code_{code}" if code else "cancelled_by_customer", self._clock.now())
                    await self._payments.save(payment)
                    self._uow.collect_events(payment.pull_events())
                    await self._uow.commit()
                return PaymentCallbackResult(payment_id, payment.status, order_ref)

            if command.provider_reference and payment.status in {PaymentStatus.REDIRECTED, PaymentStatus.UNKNOWN}:
                payment.record_provider_reference(command.provider_reference, self._clock.now())
                await self._payments.save(payment)
                await self._uow.commit()

        # A success flag in the callback proves nothing: always verify with the bank.
        status = await self._settlement.settle(payment_id)
        return PaymentCallbackResult(payment_id, status, order_ref)
