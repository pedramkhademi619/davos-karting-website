from __future__ import annotations

import uuid

from davos.modules.loyalty.application.ports.points_ledger_repository import PointsLedgerRepository
from davos.modules.loyalty.application.use_cases.points_change_result import PointsChangeResult
from davos.modules.loyalty.application.use_cases.spend_points_command import SpendPointsCommand
from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.modules.loyalty.domain.errors.insufficient_points_error import InsufficientPointsError
from davos.modules.loyalty.domain.errors.invalid_points_entry_error import InvalidPointsEntryError
from davos.modules.loyalty.domain.services.points_ledger_calculator import PointsLedgerCalculator
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class SpendPointsUseCase:
    """Redeem points. The account row lock makes balance-check-then-insert atomic per customer,
    so concurrent redemptions can never spend the same points twice."""

    def __init__(self, *, uow: UnitOfWork, ledger: PointsLedgerRepository, clock: Clock) -> None:
        self._uow = uow
        self._ledger = ledger
        self._clock = clock

    async def execute(self, command: SpendPointsCommand) -> PointsChangeResult:
        if command.points <= 0:
            raise InvalidPointsEntryError("تعداد امتیاز مصرفی باید مثبت باشد.")
        async with self._uow:
            await self._ledger.lock_account(command.customer_id)
            existing = await self._ledger.find(command.customer_id, PointsEntryKind.SPEND, command.source_ref)
            entries = await self._ledger.entries(command.customer_id)
            balance = PointsLedgerCalculator.balance(entries)
            if existing is not None:
                return PointsChangeResult(balance=balance, applied=False)
            if balance < command.points:
                raise InsufficientPointsError
            await self._ledger.append(
                PointsEntry(
                    entry_id=uuid.uuid4(),
                    customer_id=command.customer_id,
                    delta=-command.points,
                    kind=PointsEntryKind.SPEND,
                    source_ref=command.source_ref,
                    reason=command.reason,
                    created_at=self._clock.now(),
                )
            )
            await self._uow.commit()
        return PointsChangeResult(balance=balance - command.points, applied=True)
