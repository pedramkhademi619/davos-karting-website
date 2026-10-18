from __future__ import annotations

from dataclasses import dataclass

from davos.modules.accounting.domain.entities.journal_entry import JournalEntry


@dataclass(frozen=True)
class JournalPage:
    items: list[JournalEntry]
    total: int
