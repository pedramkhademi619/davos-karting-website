from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date

from davos.modules.accounting.application.ports.journal_page import JournalPage
from davos.modules.accounting.application.ports.journal_query import JournalQuery
from davos.modules.accounting.application.ports.journal_repository import JournalRepository
from davos.modules.accounting.application.services.ledger_posting_service import LedgerPostingService
from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.errors.entry_not_found_error import EntryNotFoundError
from davos.modules.accounting.domain.services.tehran_calendar import TehranCalendar
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class JournalUseCase:
    """Manual entries, reversals, and looking entries up. Posted entries are never edited or deleted."""

    def __init__(
        self, *, uow: UnitOfWork, journal: JournalRepository, posting: LedgerPostingService, clock: Clock
    ) -> None:
        self._uow = uow
        self._journal = journal
        self._posting = posting
        self._clock = clock

    async def post_manual(
        self,
        *,
        entry_date: date,
        description: str,
        lines: Sequence[JournalLine],
        created_by: str,
        opening: bool = False,
    ) -> JournalEntry:
        async with self._uow:
            entry = await self._posting.post(
                entry_date=entry_date,
                description=description,
                lines=lines,
                source=EntrySource.OPENING if opening else EntrySource.MANUAL,
                created_by=created_by,
            )
            await self._uow.commit()
        return entry

    async def reverse(self, entry_id: uuid.UUID, *, reason: str, created_by: str) -> JournalEntry:
        async with self._uow:
            await self._journal.lock_ledger()
            original = await self._journal.get(entry_id)
            if original is None:
                raise EntryNotFoundError
            lines = original.reversal_lines()
            reversal = await self._posting.post(
                entry_date=TehranCalendar.today(self._clock.now()),
                description=f"ابطال سند {original.number} ({original.fiscal_year}): {reason}".strip(),
                lines=lines,
                source=EntrySource.REVERSAL,
                source_ref=str(original.id),
                reversal_of_id=original.id,
                created_by=created_by,
            )
            original.mark_reversed(reversal.id)
            await self._journal.save_status(original)
            await self._uow.commit()
        return reversal

    async def get(self, entry_id: uuid.UUID) -> JournalEntry:
        async with self._uow:
            entry = await self._journal.get(entry_id)
        if entry is None:
            raise EntryNotFoundError
        return entry

    async def search(self, query: JournalQuery) -> JournalPage:
        async with self._uow:
            return await self._journal.search(query)
