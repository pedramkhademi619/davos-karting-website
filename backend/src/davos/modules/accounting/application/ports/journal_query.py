from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from davos.modules.accounting.domain.enums.entry_source import EntrySource


@dataclass(frozen=True)
class JournalQuery:
    date_from: date | None = None
    date_to: date | None = None
    account_id: uuid.UUID | None = None
    text: str = ""  # description or entry number
    source: EntrySource | None = None
    sources: frozenset[EntrySource] = frozenset()  # any of these (empty = no filter)
    offset: int = 0
    limit: int = 50
