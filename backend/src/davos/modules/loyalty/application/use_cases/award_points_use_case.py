from __future__ import annotations

import uuid
from datetime import timedelta

from davos.modules.loyalty.application.ports.points_ledger_repository import PointsLedgerRepository
from davos.modules.loyalty.application.use_cases.award_points_command import AwardPointsCommand
from davos.modules.loyalty.application.use_cases.points_change_result import PointsChangeResult
from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.modules.loyalty.domain.services.points_ledger_calculator import PointsLedgerCalculator
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class AwardPointsUseCase:
    """Grant points for a verified event. Replaying the same event is a harmless no-op."""

    def __init__(self, *, uow: UnitOfWork, ledger: PointsLedgerRepository, clock: Clock) -> None:
        self._uow = uow
        self._ledger = ledger
        self._clock = clock

    async def execute(self, command: AwardPointsCommand) -> PointsChangeResult:
        now = self._clock.now()
        entry = PointsEntry(
            entry_id=uuid.uuid4(),
            customer_id=command.customer_id,
            delta=command.points,
            kind=PointsEntryKind.EARN,
            source_ref=command.source_ref,
            reason=command.reason,
            created_at=now,
            expires_at=now + timedelta(days=command.expires_in_days) if command.expires_in_days else None,
        )
        async with self._uow:
            await self._ledger.lock_account(command.customer_id)
            applied = await self._ledger.append(entry)
            balance = PointsLedgerCalculator.balance(await self._ledger.entries(command.customer_id))
            await self._uow.commit()
        return PointsChangeResult(balance=balance, applied=applied)
