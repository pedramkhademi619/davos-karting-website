from __future__ import annotations

from datetime import date

from sqlalchemy import select

from davos.modules.accounting.adapters.persistence.cash_closing_model import CashClosingModel
from davos.modules.accounting.application.ports.cash_closing_repository import CashClosingRepository
from davos.modules.accounting.domain.value_objects.cash_closing import CashClosing
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

C = CashClosingModel


def _to_domain(m: CashClosingModel) -> CashClosing:
    return CashClosing(
        closing_id=m.id,
        day=m.day,
        expected_irr=m.expected_irr,
        counted_irr=m.counted_irr,
        entry_id=m.entry_id,
        note=m.note,
        closed_by=m.closed_by,
        created_at=m.created_at,
    )


class SqlAlchemyCashClosingRepository(CashClosingRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, closing: CashClosing) -> None:
        self._uow.session.add(
            CashClosingModel(
                id=closing.closing_id,
                day=closing.day,
                expected_irr=closing.expected_irr,
                counted_irr=closing.counted_irr,
                entry_id=closing.entry_id,
                note=closing.note,
                closed_by=closing.closed_by,
                created_at=closing.created_at,
            )
        )
        await self._uow.session.flush()

    async def get(self, day: date) -> CashClosing | None:
        result = await self._uow.session.execute(select(C).where(C.day == day))
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def recent(self, limit: int) -> list[CashClosing]:
        result = await self._uow.session.execute(select(C).order_by(C.day.desc()).limit(limit))
        return [_to_domain(m) for m in result.scalars()]
