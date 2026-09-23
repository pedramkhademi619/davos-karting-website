from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from davos.modules.loyalty.adapters.persistence.loyalty_account_model import LoyaltyAccountModel
from davos.modules.loyalty.adapters.persistence.points_ledger_entry_model import PointsLedgerEntryModel
from davos.modules.loyalty.application.ports.points_ledger_repository import PointsLedgerRepository
from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from davos.shared_kernel.application.clock import Clock


class SqlAlchemyPointsLedgerRepository(PointsLedgerRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def lock_account(self, customer_id: uuid.UUID) -> None:
        session = self._uow.session
        await session.execute(
            insert(LoyaltyAccountModel)
            .values(customer_id=customer_id, created_at=self._clock.now())
            .on_conflict_do_nothing(index_elements=[LoyaltyAccountModel.customer_id])
        )
        await session.execute(
            select(LoyaltyAccountModel.customer_id)
            .where(LoyaltyAccountModel.customer_id == customer_id)
            .with_for_update()
        )

    async def append(self, entry: PointsEntry) -> bool:
        statement = (
            insert(PointsLedgerEntryModel)
            .values(
                id=entry.entry_id,
                customer_id=entry.customer_id,
                delta=entry.delta,
                kind=entry.kind.value,
                source_ref=entry.source_ref,
                reason=entry.reason,
                reverses_kind=entry.reverses_kind.value if entry.reverses_kind else None,
                created_at=entry.created_at,
                expires_at=entry.expires_at,
            )
            .on_conflict_do_nothing(constraint="uq_loyalty_ledger_source")
            .returning(PointsLedgerEntryModel.id)
        )
        return (await self._uow.session.execute(statement)).scalar_one_or_none() is not None

    async def entries(self, customer_id: uuid.UUID) -> list[PointsEntry]:
        result = await self._uow.session.execute(
            select(PointsLedgerEntryModel)
            .where(PointsLedgerEntryModel.customer_id == customer_id)
            .order_by(PointsLedgerEntryModel.created_at, PointsLedgerEntryModel.id)
        )
        return [self._to_domain(m) for m in result.scalars()]

    async def find(self, customer_id: uuid.UUID, kind: PointsEntryKind, source_ref: str) -> PointsEntry | None:
        result = await self._uow.session.execute(
            select(PointsLedgerEntryModel).where(
                PointsLedgerEntryModel.customer_id == customer_id,
                PointsLedgerEntryModel.kind == kind.value,
                PointsLedgerEntryModel.source_ref == source_ref,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    @staticmethod
    def _to_domain(model: PointsLedgerEntryModel) -> PointsEntry:
        return PointsEntry(
            entry_id=model.id,
            customer_id=model.customer_id,
            delta=model.delta,
            kind=PointsEntryKind(model.kind),
            source_ref=model.source_ref,
            reason=model.reason,
            created_at=model.created_at,
            expires_at=model.expires_at,
            reverses_kind=PointsEntryKind(model.reverses_kind) if model.reverses_kind else None,
        )
