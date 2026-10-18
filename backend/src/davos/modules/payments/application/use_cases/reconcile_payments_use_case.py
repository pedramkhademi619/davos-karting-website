from __future__ import annotations

from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.application.services.payment_settlement_service import PaymentSettlementService
from davos.modules.payments.application.use_cases.reconciliation_report import ReconciliationReport
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class ReconcilePaymentsUseCase:
    """Periodic recovery: verify attempts whose verification never finished, settle paid-but-unsettled money,
    reverse money waiting for a refund and expire abandoned attempts."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        payments: PaymentRepository,
        settlement: PaymentSettlementService,
        clock: Clock,
        stuck_for_seconds: int,
        batch_size: int,
    ) -> None:
        self._uow = uow
        self._payments = payments
        self._settlement = settlement
        self._clock = clock
        self._stuck_for = stuck_for_seconds
        self._batch = batch_size

    async def execute(self) -> ReconciliationReport:
        now = self._clock.now()
        async with self._uow:
            ids = await self._payments.list_reconcilable(now=now, stuck_for_seconds=self._stuck_for, limit=self._batch)

        paid = failed = unknown = expired = 0
        for payment_id in ids:
            async with self._uow:
                payment = await self._payments.get_for_update(payment_id)
                if payment is not None and payment.is_expired_at(now):
                    payment.expire(now)
                    await self._payments.save(payment)
                    await self._uow.commit()
                    expired += 1
                    continue
                if payment is not None and payment.status is PaymentStatus.VERIFYING:
                    # A verifier crashed after claiming. Release it so settlement can claim it again.
                    payment.mark_unknown(now)
                    await self._payments.save(payment)
                    await self._uow.commit()
            status = await self._settlement.settle(payment_id)
            paid += status is PaymentStatus.PAID
            failed += status in {PaymentStatus.FAILED, PaymentStatus.REVERSED}
            unknown += status in {PaymentStatus.UNKNOWN, PaymentStatus.VERIFYING, PaymentStatus.REFUND_PENDING}
        return ReconciliationReport(examined=len(ids), paid=paid, failed=failed, still_unknown=unknown, expired=expired)
