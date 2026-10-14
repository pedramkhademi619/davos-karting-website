from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.accounting_settings_repository import AccountingSettingsRepository
from davos.modules.accounting.application.ports.journal_repository import JournalRepository
from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.errors.account_not_found_error import AccountNotFoundError
from davos.modules.accounting.domain.errors.period_locked_error import PeriodLockedError
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.shared_kernel.application.clock import Clock


class LedgerPostingService:
    """The one place entries are written: checks the period lock and every account, numbers the entry and saves it.

    Used inside the caller's unit of work, so a posting and the business change that caused it commit together.
    """

    def __init__(
        self,
        *,
        accounts: AccountRepository,
        journal: JournalRepository,
        settings: AccountingSettingsRepository,
        clock: Clock,
    ) -> None:
        self._accounts = accounts
        self._journal = journal
        self._settings = settings
        self._clock = clock

    async def post(
        self,
        *,
        entry_date: date,
        description: str,
        lines: Sequence[JournalLine],
        source: EntrySource,
        created_by: str,
        source_ref: str | None = None,
        source_date: date | None = None,
        reversal_of_id: uuid.UUID | None = None,
        allow_locked: bool = False,
    ) -> JournalEntry:
        settings = await self._settings.get()
        if not allow_locked and settings.locked_through is not None and entry_date <= settings.locked_through:
            raise PeriodLockedError
        for line in lines:
            account = await self._accounts.get(line.account_id)
            if account is None:
                raise AccountNotFoundError
            account.ensure_postable()
        fiscal_year = FiscalCalendar.year_of(entry_date)
        entry = JournalEntry.post(
            fiscal_year=fiscal_year,
            number=await self._journal.next_number(fiscal_year),
            entry_date=entry_date,
            description=description,
            lines=lines,
            source=source,
            source_ref=source_ref,
            source_date=source_date,
            reversal_of_id=reversal_of_id,
            created_by=created_by,
            now=self._clock.now(),
        )
        await self._journal.add(entry)
        return entry
