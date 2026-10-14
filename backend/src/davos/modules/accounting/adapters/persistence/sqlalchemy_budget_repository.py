from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from davos.modules.accounting.adapters.persistence.budget_model import BudgetModel
from davos.modules.accounting.application.ports.budget_repository import BudgetRepository
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

B = BudgetModel


class SqlAlchemyBudgetRepository(BudgetRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def set_amount(self, account_id: uuid.UUID, year: int, month: int, amount_irr: int) -> None:
        session = self._uow.session
        if amount_irr <= 0:
            await session.execute(delete(B).where(B.account_id == account_id, B.year == year, B.month == month))
            return
        statement = insert(B).values(account_id=account_id, year=year, month=month, amount_irr=amount_irr)
        await session.execute(
            statement.on_conflict_do_update(
                index_elements=["account_id", "year", "month"], set_={"amount_irr": amount_irr}
            )
        )

    async def for_year(self, year: int) -> dict[tuple[uuid.UUID, int], int]:
        result = await self._uow.session.execute(select(B).where(B.year == year))
        return {(m.account_id, m.month): m.amount_irr for m in result.scalars()}
