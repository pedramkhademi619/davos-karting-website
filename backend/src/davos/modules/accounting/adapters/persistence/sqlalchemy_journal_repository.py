from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import date

from sqlalchemy import String as SaString
from sqlalchemy import and_, cast, exists, func, or_, select, text, update

from davos.modules.accounting.adapters.persistence.account_model import AccountModel
from davos.modules.accounting.adapters.persistence.journal_entry_model import JournalEntryModel
from davos.modules.accounting.adapters.persistence.journal_line_model import JournalLineModel
from davos.modules.accounting.application.ports.journal_page import JournalPage
from davos.modules.accounting.application.ports.journal_query import JournalQuery
from davos.modules.accounting.application.ports.journal_repository import JournalRepository
from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.enums.entry_status import EntryStatus
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

E = JournalEntryModel
L = JournalLineModel


def _to_domain(m: JournalEntryModel, lines: Sequence[JournalLineModel]) -> JournalEntry:
    return JournalEntry(
        entry_id=m.id,
        fiscal_year=m.fiscal_year,
        number=m.number,
        entry_date=m.entry_date,
        description=m.description,
        source=EntrySource(m.source),
        source_ref=m.source_ref,
        source_date=m.source_date,
        lines=[
            JournalLine(
                account_id=line.account_id,
                debit_irr=line.debit_irr,
                credit_irr=line.credit_irr,
                memo=line.memo,
                party_id=line.party_id,
            )
            for line in sorted(lines, key=lambda item: item.line_no)
        ],
        status=EntryStatus(m.status),
        reversed_by_id=m.reversed_by_id,
        reversal_of_id=m.reversal_of_id,
        created_by=m.created_by,
        created_at=m.created_at,
    )


class SqlAlchemyJournalRepository(JournalRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def next_number(self, fiscal_year: int) -> int:
        result = await self._uow.session.execute(
            text(
                "INSERT INTO accounting_counters (key, value) VALUES (:key, 1) "
                "ON CONFLICT (key) DO UPDATE SET value = accounting_counters.value + 1 RETURNING value"
            ),
            {"key": f"journal:{fiscal_year}"},
        )
        return int(result.scalar_one())

    async def add(self, entry: JournalEntry) -> None:
        session = self._uow.session
        session.add(
            JournalEntryModel(
                id=entry.id,
                fiscal_year=entry.fiscal_year,
                number=entry.number,
                entry_date=entry.entry_date,
                description=entry.description,
                source=entry.source.value,
                source_ref=entry.source_ref,
                source_date=entry.source_date,
                status=entry.status.value,
                reversed_by_id=entry.reversed_by_id,
                reversal_of_id=entry.reversal_of_id,
                created_by=entry.created_by,
                created_at=entry.created_at,
            )
        )
        await session.flush()
        for index, line in enumerate(entry.lines, start=1):
            session.add(
                JournalLineModel(
                    entry_id=entry.id,
                    line_no=index,
                    account_id=line.account_id,
                    debit_irr=line.debit_irr,
                    credit_irr=line.credit_irr,
                    memo=line.memo,
                    party_id=line.party_id,
                )
            )
        await session.flush()

    async def save_status(self, entry: JournalEntry) -> None:
        await self._uow.session.execute(
            update(E).where(E.id == entry.id).values(status=entry.status.value, reversed_by_id=entry.reversed_by_id)
        )

    async def _lines_of(self, entry_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, list[JournalLineModel]]:
        grouped: dict[uuid.UUID, list[JournalLineModel]] = defaultdict(list)
        if entry_ids:
            result = await self._uow.session.execute(select(L).where(L.entry_id.in_(entry_ids)))
            for line in result.scalars():
                grouped[line.entry_id].append(line)
        return grouped

    async def get(self, entry_id: uuid.UUID) -> JournalEntry | None:
        model = await self._uow.session.get(E, entry_id)
        if model is None:
            return None
        return _to_domain(model, (await self._lines_of([entry_id]))[entry_id])

    async def find_by_source(self, source: EntrySource, source_ref: str) -> JournalEntry | None:
        result = await self._uow.session.execute(
            select(E).where(E.source == source.value, E.source_ref == source_ref).limit(1)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _to_domain(model, (await self._lines_of([model.id]))[model.id])

    async def search(self, query: JournalQuery) -> JournalPage:
        conditions = []
        if query.date_from:
            conditions.append(E.entry_date >= query.date_from)
        if query.date_to:
            conditions.append(E.entry_date <= query.date_to)
        if query.source:
            conditions.append(E.source == query.source.value)
        if query.sources:
            conditions.append(E.source.in_(sorted(s.value for s in query.sources)))
        if query.account_id:
            conditions.append(exists().where(L.entry_id == E.id, L.account_id == query.account_id))
        needle = query.text.strip()
        if needle:
            clauses = [E.description.ilike(f"%{needle}%"), cast(E.source_ref, SaString) == needle]
            if needle.isdigit():
                clauses.append(E.number == int(needle))
            conditions.append(or_(*clauses))
        where = and_(*conditions) if conditions else text("true")
        total = (await self._uow.session.execute(select(func.count()).select_from(E).where(where))).scalar_one()
        result = await self._uow.session.execute(
            select(E)
            .where(where)
            .order_by(E.entry_date.desc(), E.fiscal_year.desc(), E.number.desc())
            .offset(max(query.offset, 0))
            .limit(min(max(query.limit, 1), 200))
        )
        models = list(result.scalars())
        lines = await self._lines_of([m.id for m in models])
        return JournalPage([_to_domain(m, lines[m.id]) for m in models], int(total))

    async def unrecognized_sales(self, through: date, limit: int) -> list[JournalEntry]:
        deferred = exists().where(
            L.entry_id == E.id,
            L.credit_irr > 0,
            L.account_id.in_(select(AccountModel.id).where(AccountModel.role == "deferred_revenue")),
        )
        later = JournalEntryModel.__table__.alias("later")
        settled = exists().where(later.c.source_ref == E.source_ref, later.c.source.in_(["recognition", "refund"]))
        result = await self._uow.session.execute(
            select(E)
            .where(
                E.source.in_(["online_sale", "counter_sale"]),
                E.status == "posted",
                E.source_date <= through,
                deferred,
                ~settled,
            )
            .order_by(E.source_date, E.number)
            .limit(limit)
        )
        models = list(result.scalars())
        lines = await self._lines_of([m.id for m in models])
        return [_to_domain(m, lines[m.id]) for m in models]

    async def lock_ledger(self) -> None:
        await self._uow.session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('accounting-ledger', 0))"))
