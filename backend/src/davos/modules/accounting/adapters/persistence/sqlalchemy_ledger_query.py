from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import date
from typing import Any

from sqlalchemy import case, func, literal, select

from davos.modules.accounting.adapters.persistence.account_model import AccountModel
from davos.modules.accounting.adapters.persistence.journal_entry_model import JournalEntryModel
from davos.modules.accounting.adapters.persistence.journal_line_model import JournalLineModel
from davos.modules.accounting.application.ports.account_ledger import AccountLedger
from davos.modules.accounting.application.ports.ledger_query import LedgerQuery
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.value_objects.account_balance import AccountBalance
from davos.modules.accounting.domain.value_objects.ledger_line import LedgerLine
from davos.modules.accounting.domain.value_objects.party_line import PartyLine
from davos.modules.accounting.domain.value_objects.revenue_day import RevenueDay
from davos.modules.accounting.domain.value_objects.sales_receipt import SalesReceipt
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

E = JournalEntryModel
L = JournalLineModel
A = AccountModel

_CASH_ROLES = ("cash", "bank", "pos", "gateway")


class SqlAlchemyLedgerQuery(LedgerQuery):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def balances(
        self, date_from: date | None, date_to: date, exclude_sources: Collection[EntrySource] = ()
    ) -> list[AccountBalance]:
        opening: Any
        if date_from is None:
            opening = literal(0)
            debit = func.coalesce(func.sum(L.debit_irr), 0)
            credit = func.coalesce(func.sum(L.credit_irr), 0)
        else:
            opening = func.coalesce(func.sum(case((E.entry_date < date_from, L.debit_irr - L.credit_irr), else_=0)), 0)
            debit = func.coalesce(func.sum(case((E.entry_date >= date_from, L.debit_irr), else_=0)), 0)
            credit = func.coalesce(func.sum(case((E.entry_date >= date_from, L.credit_irr), else_=0)), 0)
        statement = (
            select(L.account_id, opening, debit, credit).join(E, E.id == L.entry_id).where(E.entry_date <= date_to)
        )
        if exclude_sources:
            statement = statement.where(E.source.not_in([s.value for s in exclude_sources]))
        result = await self._uow.session.execute(statement.group_by(L.account_id))
        return [AccountBalance(account_id, int(o), int(d), int(c)) for account_id, o, d, c in result.all()]

    async def account_ledger(self, account_ids: Collection[uuid.UUID], date_from: date, date_to: date) -> AccountLedger:
        session = self._uow.session
        opening = (
            await session.execute(
                select(func.coalesce(func.sum(L.debit_irr - L.credit_irr), 0))
                .join(E, E.id == L.entry_id)
                .where(L.account_id.in_(account_ids), E.entry_date < date_from)
            )
        ).scalar_one()
        result = await session.execute(
            select(L, E)
            .join(E, E.id == L.entry_id)
            .where(L.account_id.in_(account_ids), E.entry_date >= date_from, E.entry_date <= date_to)
            .order_by(E.entry_date, E.fiscal_year, E.number, L.line_no)
        )
        lines = [
            LedgerLine(
                entry_id=e.id,
                entry_number=e.number,
                fiscal_year=e.fiscal_year,
                entry_date=e.entry_date,
                description=e.description,
                memo=line.memo,
                debit_irr=line.debit_irr,
                credit_irr=line.credit_irr,
                source=e.source,
                party_id=line.party_id,
            )
            for line, e in result.all()
        ]
        return AccountLedger(int(opening), lines)

    async def party_lines(self, account_id: uuid.UUID, as_of: date) -> list[PartyLine]:
        result = await self._uow.session.execute(
            select(L.party_id, E.entry_date, L.debit_irr, L.credit_irr)
            .join(E, E.id == L.entry_id)
            .where(L.account_id == account_id, L.party_id.is_not(None), E.entry_date <= as_of)
        )
        return [PartyLine(party, day, int(d), int(c)) for party, day, d, c in result.all()]

    async def sales_receipts(self, date_from: date, date_to: date) -> list[SalesReceipt]:
        result = await self._uow.session.execute(
            select(E.entry_date, E.source, A.role, func.sum(L.debit_irr))
            .join(E, E.id == L.entry_id)
            .join(A, A.id == L.account_id)
            .where(
                E.entry_date >= date_from,
                E.entry_date <= date_to,
                E.source.in_(["online_sale", "counter_sale"]),
                E.status == "posted",
                A.role.in_(_CASH_ROLES),
                L.debit_irr > 0,
            )
            .group_by(E.entry_date, E.source, A.role)
            .order_by(E.entry_date)
        )
        return [SalesReceipt(day, source, role, int(amount)) for day, source, role, amount in result.all()]

    async def revenue_by_day(self, date_from: date, date_to: date) -> list[RevenueDay]:
        result = await self._uow.session.execute(
            select(E.entry_date, E.source, func.sum(L.credit_irr - L.debit_irr))
            .join(E, E.id == L.entry_id)
            .join(A, A.id == L.account_id)
            .where(E.entry_date >= date_from, E.entry_date <= date_to, A.type == "revenue", E.source != "closing")
            .group_by(E.entry_date, E.source)
            .order_by(E.entry_date)
        )
        return [RevenueDay(day, source, int(amount)) for day, source, amount in result.all()]
