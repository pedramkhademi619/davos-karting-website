from __future__ import annotations

import uuid

from davos.modules.loyalty.application.ports.points_ledger_repository import PointsLedgerRepository
from davos.modules.loyalty.application.use_cases.points_change_result import PointsChangeResult
from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.modules.loyalty.domain.services.points_ledger_calculator import PointsLedgerCalculator
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class ReversePointsUseCase:
    """Compensate an earlier entry (cancellation, refund). The original line is never edited or deleted."""

    def __init__(self, *, uow: UnitOfWork, ledger: PointsLedgerRepository, clock: Clock) -> None:
        self._uow = uow
        self._ledger = ledger
        self._clock = clock

    async def execute(
        self, *, customer_id: uuid.UUID, original_kind: PointsEntryKind, original_source_ref: str, reason: str
    ) -> PointsChangeResult:
        async with self._uow:
            await self._ledger.lock_account(customer_id)
            original = await self._ledger.find(customer_id, original_kind, original_source_ref)
            if original is None:
                raise NotFoundError("تراکنش امتیاز موردنظر یافت نشد.")
            applied = await self._ledger.append(
                PointsEntry(
                    entry_id=uuid.uuid4(),
                    customer_id=customer_id,
                    delta=-original.delta,
                    kind=PointsEntryKind.REVERSAL,
                    source_ref=f"reversal:{original_kind.value}:{original_source_ref}",
                    reason=reason,
                    created_at=self._clock.now(),
                    reverses_kind=original_kind,
                )
            )
            balance = PointsLedgerCalculator.balance(await self._ledger.entries(customer_id))
            await self._uow.commit()
        return PointsChangeResult(balance=balance, applied=applied)
