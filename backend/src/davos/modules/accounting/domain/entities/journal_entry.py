from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, datetime

from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.enums.entry_status import EntryStatus
from davos.modules.accounting.domain.errors.empty_entry_error import EmptyEntryError
from davos.modules.accounting.domain.errors.entry_already_reversed_error import EntryAlreadyReversedError
from davos.modules.accounting.domain.errors.entry_not_reversible_error import EntryNotReversibleError
from davos.modules.accounting.domain.errors.unbalanced_entry_error import UnbalancedEntryError
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.shared_kernel.domain.entity import Entity


class JournalEntry(Entity[uuid.UUID]):
    """A balanced posting (سند حسابداری). Its lines never change once posted; a mistake is undone by a reversal."""

    def __init__(
        self,
        *,
        entry_id: uuid.UUID,
        fiscal_year: int,
        number: int,
        entry_date: date,
        description: str,
        source: EntrySource,
        source_ref: str | None,
        source_date: date | None,
        lines: Sequence[JournalLine],
        status: EntryStatus,
        reversed_by_id: uuid.UUID | None,
        reversal_of_id: uuid.UUID | None,
        created_by: str,
        created_at: datetime,
    ) -> None:
        super().__init__(entry_id)
        self.fiscal_year = fiscal_year
        self.number = number
        self.entry_date = entry_date
        self.description = " ".join(description.split())[:300]
        self.source = source
        self.source_ref = source_ref
        self.source_date = source_date
        self.lines = tuple(lines)
        self.status = status
        self.reversed_by_id = reversed_by_id
        self.reversal_of_id = reversal_of_id
        self.created_by = created_by
        self.created_at = created_at

    @classmethod
    def post(
        cls,
        *,
        fiscal_year: int,
        number: int,
        entry_date: date,
        description: str,
        lines: Sequence[JournalLine],
        source: EntrySource,
        source_ref: str | None = None,
        source_date: date | None = None,
        reversal_of_id: uuid.UUID | None = None,
        created_by: str,
        now: datetime,
    ) -> JournalEntry:
        if len(lines) < 2:
            raise EmptyEntryError
        if sum(line.debit_irr for line in lines) != sum(line.credit_irr for line in lines):
            raise UnbalancedEntryError
        return cls(
            entry_id=uuid.uuid4(),
            fiscal_year=fiscal_year,
            number=number,
            entry_date=entry_date,
            description=description,
            source=source,
            source_ref=source_ref,
            source_date=source_date,
            lines=lines,
            status=EntryStatus.POSTED,
            reversed_by_id=None,
            reversal_of_id=reversal_of_id,
            created_by=created_by,
            created_at=now,
        )

    @property
    def total_irr(self) -> int:
        return sum(line.debit_irr for line in self.lines)

    def reversal_lines(self) -> list[JournalLine]:
        """The same lines with debit and credit swapped, which cancels this entry exactly."""
        if self.status is EntryStatus.REVERSED:
            raise EntryAlreadyReversedError
        if self.source in (EntrySource.REVERSAL, EntrySource.CLOSING):
            raise EntryNotReversibleError
        return [
            JournalLine(
                account_id=line.account_id,
                debit_irr=line.credit_irr,
                credit_irr=line.debit_irr,
                memo=line.memo,
                party_id=line.party_id,
            )
            for line in self.lines
        ]

    def mark_reversed(self, by_id: uuid.UUID) -> None:
        if self.status is EntryStatus.REVERSED:
            raise EntryAlreadyReversedError
        self.status = EntryStatus.REVERSED
        self.reversed_by_id = by_id
