from __future__ import annotations

from davos.modules.payments.application.ports.gateway_error import GatewayError
from davos.modules.payments.application.ports.order_quote_port import OrderQuotePort
from davos.modules.payments.application.ports.payment_gateway_port import PaymentGatewayPort
from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.application.ports.payment_request import PaymentRequest
from davos.modules.payments.application.use_cases.start_payment_command import StartPaymentCommand
from davos.modules.payments.application.use_cases.start_payment_result import StartPaymentResult
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.modules.payments.domain.errors.payment_not_found_error import PaymentNotFoundError
from davos.modules.payments.domain.errors.payments_disabled_error import PaymentsDisabledError
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class StartPaymentUseCase:
    """Create a payment attempt for a server-quoted order and obtain the gateway redirect."""

    def __init__(
        self,
        *,
        enabled: bool,
        uow: UnitOfWork,
        payments: PaymentRepository,
        quotes: OrderQuotePort,
        gateway: PaymentGatewayPort,
        clock: Clock,
        callback_url: str,
    ) -> None:
        self._enabled = enabled
        self._uow = uow
        self._payments = payments
        self._quotes = quotes
        self._gateway = gateway
        self._clock = clock
        self._callback_url = callback_url

    async def execute(self, command: StartPaymentCommand) -> StartPaymentResult:
        if not self._enabled:
            raise PaymentsDisabledError
        quote = await self._quotes.quote(command.order_ref, command.customer_id)
        if quote is None:
            raise PaymentNotFoundError  # unknown order, or an order that belongs to someone else

        async with self._uow:
            if await self._payments.has_paid_for_order(command.order_ref):
                raise ConflictError("این سفارش قبلا پرداخت شده است.", code="order_already_paid")

        now = self._clock.now()
        payment = PaymentAttempt.create(
            order_ref=command.order_ref, customer_id=command.customer_id, amount=quote.amount, now=now
        )
        async with self._uow:
            await self._payments.add(payment)
            await self._uow.commit()

        try:
            session = await self._gateway.request_payment(
                PaymentRequest(
                    payment_id=str(payment.id),
                    order_ref=payment.order_ref,
                    amount=payment.amount,
                    description=quote.description,
                    callback_url=self._callback_url,
                )
            )
        except GatewayError as exc:
            async with self._uow:
                stored = await self._payments.get_for_update(payment.id)
                if stored is not None:
                    stored.mark_failed("gateway_request_failed", self._clock.now())
                    await self._payments.save(stored)
                    self._uow.collect_events(stored.pull_events())
                    await self._uow.commit()
            raise ConflictError(
                "امکان شروع پرداخت وجود ندارد. لطفا بعدا تلاش کنید.", code="payment_start_failed"
            ) from exc

        async with self._uow:
            stored = await self._payments.get_for_update(payment.id)
            if stored is None:  # pragma: no cover - cannot vanish inside this flow
                raise PaymentNotFoundError
            stored.mark_redirected(session.authority, self._clock.now())
            await self._payments.save(stored)
            await self._uow.commit()
        return StartPaymentResult(payment_id=payment.id, redirect_url=session.redirect_url)
