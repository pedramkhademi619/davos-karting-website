from __future__ import annotations

import uuid

from davos.modules.loyalty.application.ports.points_ledger_repository import PointsLedgerRepository
from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.modules.loyalty.domain.services.points_ledger_calculator import PointsLedgerCalculator
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class ExpirePointsUseCase:
    """Scheduled expiry: appends an EXPIRE line for unspent points past their date (idempotent per day)."""

    def __init__(self, *, uow: UnitOfWork, ledger: PointsLedgerRepository, clock: Clock) -> None:
        self._uow = uow
        self._ledger = ledger
        self._clock = clock

    async def execute(self, customer_id: uuid.UUID) -> int:
        now = self._clock.now()
        async with self._uow:
            await self._ledger.lock_account(customer_id)
            expirable = PointsLedgerCalculator.expirable(await self._ledger.entries(customer_id), now)
            if expirable <= 0:
                return 0
            appended = await self._ledger.append(
                PointsEntry(
                    entry_id=uuid.uuid4(),
                    customer_id=customer_id,
                    delta=-expirable,
                    kind=PointsEntryKind.EXPIRE,
                    source_ref=f"expiry:{now.date().isoformat()}",
                    reason="points expired",
                    created_at=now,
                )
            )
            await self._uow.commit()
            return expirable if appended else 0
