from __future__ import annotations

import uuid
from datetime import timedelta

from davos.modules.loyalty.application.ports.points_ledger_repository import PointsLedgerRepository
from davos.modules.loyalty.application.use_cases.loyalty_summary import LoyaltySummary
from davos.modules.loyalty.domain.services.points_ledger_calculator import PointsLedgerCalculator
from davos.modules.loyalty.domain.services.tier_ladder import TierLadder
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class GetLoyaltySummaryUseCase:
    def __init__(self, *, uow: UnitOfWork, ledger: PointsLedgerRepository, ladder: TierLadder, clock: Clock) -> None:
        self._uow = uow
        self._ledger = ledger
        self._ladder = ladder
        self._clock = clock

    async def execute(self, customer_id: uuid.UUID, *, expiry_notice_days: int = 30) -> LoyaltySummary:
        now = self._clock.now()
        async with self._uow:
            entries = await self._ledger.entries(customer_id)
        lifetime = PointsLedgerCalculator.lifetime_earned(entries)
        tier = self._ladder.tier_for(lifetime)
        upcoming = self._ladder.next_tier(lifetime)
        return LoyaltySummary(
            balance=PointsLedgerCalculator.balance(entries),
            lifetime_points=lifetime,
            tier_name=tier.name,
            next_tier_name=upcoming.name if upcoming else None,
            points_to_next_tier=upcoming.min_lifetime_points - lifetime if upcoming else None,
            expiring_soon=PointsLedgerCalculator.expiring_within(
                entries, now, now + timedelta(days=expiry_notice_days)
            ),
        )
