from __future__ import annotations

import logging
import uuid

from davos.modules.payments.application.ports.gateway_error import GatewayError
from davos.modules.payments.application.ports.payment_gateway_port import PaymentGatewayPort
from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.application.ports.verification_outcome import VerificationOutcome
from davos.modules.payments.application.ports.verification_request import VerificationRequest
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.money import Money

logger = logging.getLogger(__name__)


class PaymentSettlementService:
    """Turns an attempt into PAID / FAILED / UNKNOWN through server-to-server verification.

    Shared by the browser callback and the reconciliation job so both follow the same rules:

    1. Claim the attempt by moving it to VERIFYING inside a row-locked transaction and commit.
       A concurrent caller sees VERIFYING and returns without calling the provider, so a payment
       is verified (and recorded as successful) exactly once.
    2. Call the provider outside any database transaction (network I/O never holds a lock).
    3. Record the outcome; a timeout or outage becomes UNKNOWN, never FAILED.
    """

    def __init__(
        self, *, uow: UnitOfWork, payments: PaymentRepository, gateway: PaymentGatewayPort, clock: Clock
    ) -> None:
        self._uow = uow
        self._payments = payments
        self._gateway = gateway
        self._clock = clock

    async def settle(self, payment_id: uuid.UUID) -> PaymentStatus:
        claimed = await self._claim(payment_id)
        if claimed is None:
            return await self._current_status(payment_id)
        authority, amount = claimed

        try:
            result = await self._gateway.verify_payment(VerificationRequest(authority=authority, amount=amount))
        except GatewayError:  # timeout, outage or malformed answer: the outcome is unknown, never 'failed'
            return await self._record_unknown(payment_id)
        return await self._record_result(payment_id, result.outcome, result.reference_id)

    async def _claim(self, payment_id: uuid.UUID) -> tuple[str, Money] | None:
        now = self._clock.now()
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None or payment.authority is None:
                return None
            if payment.status not in {PaymentStatus.REDIRECTED, PaymentStatus.UNKNOWN}:
                return None  # already settled, or another worker is verifying right now
            payment.begin_verification(now)
            await self._payments.save(payment)
            await self._uow.commit()
            return payment.authority, payment.amount

    async def _current_status(self, payment_id: uuid.UUID) -> PaymentStatus:
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            return payment.status if payment else PaymentStatus.FAILED

    async def _record_unknown(self, payment_id: uuid.UUID) -> PaymentStatus:
        now = self._clock.now()
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None:
                return PaymentStatus.UNKNOWN
            payment.mark_unknown(now)
            await self._payments.save(payment)
            await self._uow.commit()
            logger.warning("payment verification inconclusive; left for reconciliation")
            return payment.status

    async def _record_result(
        self, payment_id: uuid.UUID, outcome: VerificationOutcome, reference_id: str | None
    ) -> PaymentStatus:
        now = self._clock.now()
        async with self._uow:
            payment = await self._payments.get_for_update(payment_id)
            if payment is None:
                return PaymentStatus.FAILED
            if outcome in {VerificationOutcome.VERIFIED, VerificationOutcome.ALREADY_VERIFIED}:
                payment.mark_paid(reference_id or "", now)
            else:
                payment.mark_failed("verification_rejected", now)
            await self._payments.save(payment)
            self._uow.collect_events(payment.pull_events())
            await self._uow.commit()
            return payment.status
