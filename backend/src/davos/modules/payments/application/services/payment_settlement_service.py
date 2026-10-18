from __future__ import annotations

import logging
import uuid

from davos.modules.payments.application.ports.gateway_error import GatewayError
from davos.modules.payments.application.ports.order_quote_port import OrderQuotePort
from davos.modules.payments.application.ports.payment_gateway_port import PaymentGatewayPort
from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.application.ports.settlement_outcome import SettlementOutcome
from davos.modules.payments.application.ports.verification_outcome import VerificationOutcome
from davos.modules.payments.application.ports.verification_request import VerificationRequest
from davos.modules.payments.application.services.settlement_claim import SettlementClaim
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class PaymentSettlementService:
    """Turns an attempt into PAID / FAILED / UNKNOWN / REFUND_PENDING, settles accepted money and reverses the rest.

    Shared by the browser callback and the reconciliation job so both follow the same rules:

    1. Claim the attempt by moving it to VERIFYING inside a row-locked transaction. A concurrent caller sees
       VERIFYING and returns without calling the bank, so each payment is verified exactly once.
    2. Verify with the bank outside any database transaction (network I/O never holds a lock). Timeouts and
       outages become UNKNOWN, never FAILED.
    3. Ask the order whether it still accepts this exact amount, then, under a per-order lock, record PAID only if no
       other attempt already paid the order. Otherwise the attempt becomes REFUND_PENDING.
    4. Settle PAID money / reverse REFUND_PENDING money. Both are retried by reconciliation until the bank answers.
    """

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        payments: PaymentRepository,
        gateway: PaymentGatewayPort,
        orders: OrderQuotePort,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._payments = payments
        self._gateway = gateway
        self._orders = orders
        self._clock = clock

    async def settle(self, payment_id: uuid.UUID) -> PaymentStatus:
        claim = await self._claim(payment_id)
        if claim is None:
            return await self.finish(payment_id)

        try:
            result = await self._gateway.verify_payment(claim.request)
        except GatewayError:  # timeout, outage or malformed answer: the outcome is unknown, never 'failed'
            return await self._record_unknown(payment_id)
        if result.outcome is VerificationOutcome.REJECTED:
            return await self._record_failed(payment_id, f"verification_rejected_{result.provider_code}")

        reference = result.reference_id or claim.request.provider_reference or claim.request.authority
        try:
            accepted = await self._orders.accepts_payment(claim.order_ref, claim.customer_id, claim.amount)
        except Exception:  # our own order service failed: keep the money safe and decide later
            logger.exception("order check failed after a verified payment; left for reconciliation")
            return await self._record_unknown(payment_id)
        await self._record_verified(payment_id, reference, accepted)
        return await self.finish(payment_id)

    async def finish(self, payment_id: uuid.UUID) -> PaymentStatus:
        """Settle an accepted payment or reverse a refused one. Safe to call any number of times."""
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None:
                return PaymentStatus.FAILED
            request = self._request(payment)
            if payment.needs_settlement:
                action = "settle"
            elif payment.status is PaymentStatus.REFUND_PENDING:
                action = "reverse"
            else:
                return payment.status

        if action == "settle":
            return await self._settle(payment_id, request)
        return await self._reverse(payment_id, request)

    async def _claim(self, payment_id: uuid.UUID) -> SettlementClaim | None:
        now = self._clock.now()
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None or payment.authority is None:
                return None
            if payment.status not in {PaymentStatus.REDIRECTED, PaymentStatus.UNKNOWN}:
                return None  # already decided, or another worker is verifying right now
            payment.begin_verification(now)
            await self._payments.save(payment)
            await self._uow.commit()
            return SettlementClaim(self._request(payment), payment.order_ref, payment.customer_id, payment.amount)

    async def _record_verified(self, payment_id: uuid.UUID, reference: str, accepted: bool) -> None:
        now = self._clock.now()
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None or payment.status is not PaymentStatus.VERIFYING:
                return
            await self._payments.lock_order(payment.order_ref)
            already_paid = await self._payments.has_paid_for_order(payment.order_ref, excluding=payment.id)
            if already_paid:
                logger.warning("second verified payment for one order; it will be reversed")
                payment.mark_refund_pending("duplicate_payment", reference or None, now)
            elif not accepted:
                logger.warning("verified payment for an order that no longer accepts it; it will be reversed")
                payment.mark_refund_pending("order_not_payable", reference or None, now)
            else:
                payment.mark_paid(reference, now)
            await self._payments.save(payment)
            self._uow.collect_events(payment.pull_events())
            await self._uow.commit()

    async def _settle(self, payment_id: uuid.UUID, request: VerificationRequest) -> PaymentStatus:
        try:
            outcome = await self._gateway.settle_payment(request)
        except GatewayError:
            logger.warning("settlement answer unknown; reconciliation will retry")
            return PaymentStatus.PAID
        now = self._clock.now()
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None or not payment.needs_settlement:
                return payment.status if payment else PaymentStatus.FAILED
            if outcome is SettlementOutcome.SETTLED:
                payment.mark_settled(now)
            elif outcome is SettlementOutcome.REVERSED:
                logger.error("the bank reversed a paid payment before it was settled")
                payment.mark_reversed(now)
            else:
                return payment.status
            await self._payments.save(payment)
            self._uow.collect_events(payment.pull_events())
            await self._uow.commit()
            return payment.status

    async def _reverse(self, payment_id: uuid.UUID, request: VerificationRequest) -> PaymentStatus:
        try:
            reversed_ = await self._gateway.reverse_payment(request)
        except GatewayError:
            logger.warning("reversal answer unknown; reconciliation will retry")
            return PaymentStatus.REFUND_PENDING
        if not reversed_:
            logger.error("the bank refused a reversal; refund this payment by hand")
            return PaymentStatus.REFUND_PENDING
        now = self._clock.now()
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None or payment.status is not PaymentStatus.REFUND_PENDING:
                return payment.status if payment else PaymentStatus.FAILED
            payment.mark_reversed(now)
            await self._payments.save(payment)
            self._uow.collect_events(payment.pull_events())
            await self._uow.commit()
            return payment.status

    async def _record_unknown(self, payment_id: uuid.UUID) -> PaymentStatus:
        now = self._clock.now()
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None:
                return PaymentStatus.UNKNOWN
            if payment.status is PaymentStatus.VERIFYING:
                payment.mark_unknown(now)
                await self._payments.save(payment)
                await self._uow.commit()
            logger.warning("payment verification inconclusive; left for reconciliation")
            return payment.status

    async def _record_failed(self, payment_id: uuid.UUID, reason: str) -> PaymentStatus:
        now = self._clock.now()
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None:
                return PaymentStatus.FAILED
            if payment.status is PaymentStatus.VERIFYING:
                payment.mark_failed(reason, now)
                await self._payments.save(payment)
                self._uow.collect_events(payment.pull_events())
                await self._uow.commit()
            return payment.status

    @staticmethod
    def _request(payment: PaymentAttempt) -> VerificationRequest:
        return VerificationRequest(
            authority=payment.authority or "",
            amount=payment.amount,
            gateway_order_id=payment.gateway_order_id,
            provider_reference=payment.provider_reference,
        )
