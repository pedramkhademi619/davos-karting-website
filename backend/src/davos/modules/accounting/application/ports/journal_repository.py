from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date

from davos.modules.accounting.application.ports.journal_page import JournalPage
from davos.modules.accounting.application.ports.journal_query import JournalQuery
from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.enums.entry_source import EntrySource


class JournalRepository(ABC):
    @abstractmethod
    async def next_number(self, fiscal_year: int) -> int:
        """The next gapless document number of the fiscal year (the counter row is locked until commit)."""

    @abstractmethod
    async def add(self, entry: JournalEntry) -> None: ...

    @abstractmethod
    async def save_status(self, entry: JournalEntry) -> None: ...

    @abstractmethod
    async def get(self, entry_id: uuid.UUID) -> JournalEntry | None: ...

    @abstractmethod
    async def find_by_source(self, source: EntrySource, source_ref: str) -> JournalEntry | None: ...

    @abstractmethod
    async def search(self, query: JournalQuery) -> JournalPage: ...

    @abstractmethod
    async def unrecognized_sales(self, through: date, limit: int) -> list[JournalEntry]:
        """Ticket sales parked as customer advances whose session day has come but whose revenue is not yet earned."""

    @abstractmethod
    async def lock_ledger(self) -> None:
        """Serialise changes that depend on the whole ledger (year-end closing, cash count)."""
