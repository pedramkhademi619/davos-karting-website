from __future__ import annotations

from dataclasses import replace

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.accounting_settings_repository import AccountingSettingsRepository
from davos.modules.accounting.application.ports.journal_repository import JournalRepository
from davos.modules.accounting.application.ports.ledger_query import LedgerQuery
from davos.modules.accounting.application.services.ledger_posting_service import LedgerPostingService
from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.errors.missing_system_account_error import MissingSystemAccountError
from davos.modules.accounting.domain.errors.year_already_closed_error import YearAlreadyClosedError
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.modules.accounting.domain.services.tehran_calendar import TehranCalendar
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.validation_error import ValidationError


class FiscalYearUseCase:
    """Year-end: the year's revenue and expense accounts are zeroed into retained earnings by one closing entry, and the
    year is locked. The year's statements still show its profit because they leave closing entries out."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        accounts: AccountRepository,
        journal: JournalRepository,
        ledger: LedgerQuery,
        settings: AccountingSettingsRepository,
        posting: LedgerPostingService,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._accounts = accounts
        self._journal = journal
        self._ledger = ledger
        self._settings = settings
        self._posting = posting
        self._clock = clock

    async def is_closed(self, year: int) -> bool:
        async with self._uow:
            return await self._journal.find_by_source(EntrySource.CLOSING, str(year)) is not None

    async def close_year(self, year: int, *, closed_by: str) -> JournalEntry:
        year_end = FiscalCalendar.year_end(year)
        if year_end >= TehranCalendar.today(self._clock.now()):
            raise ValidationError("سال مالی هنوز تمام نشده و بستن آن ممکن نیست.", code="year_not_finished")
        async with self._uow:
            await self._journal.lock_ledger()
            if await self._journal.find_by_source(EntrySource.CLOSING, str(year)) is not None:
                raise YearAlreadyClosedError
            roles = await self._accounts.roles()
            retained = roles.get(AccountRole.RETAINED_EARNINGS)
            if retained is None:
                raise MissingSystemAccountError
            accounts = {a.id: a for a in await self._accounts.list_all()}
            balances = await self._ledger.balances(FiscalCalendar.year_start(year), year_end, [EntrySource.CLOSING])
            lines: list[JournalLine] = []
            profit = 0
            memo = f"بستن حساب‌های موقت سال {year}"
            for b in balances:
                account = accounts.get(b.account_id)
                net = b.debit - b.credit
                if account is None or not account.type.is_temporary or net == 0:
                    continue
                profit -= net
                lines.append(
                    JournalLine(account.id, credit_irr=net, memo=memo)
                    if net > 0
                    else JournalLine(account.id, debit_irr=-net, memo=memo)
                )
            if not lines:
                raise ValidationError("در این سال درآمد یا هزینه‌ای برای بستن وجود ندارد.", code="nothing_to_close")
            if profit:
                lines.append(
                    JournalLine(retained, credit_irr=profit, memo=memo)
                    if profit > 0
                    else JournalLine(retained, debit_irr=-profit, memo=memo)
                )
            entry = await self._posting.post(
                entry_date=year_end,
                description=memo,
                lines=lines,
                source=EntrySource.CLOSING,
                source_ref=str(year),
                created_by=closed_by,
                allow_locked=True,
            )
            settings = await self._settings.get()
            if settings.locked_through is None or settings.locked_through < year_end:
                await self._settings.save(replace(settings, locked_through=year_end), self._clock.now())
            await self._uow.commit()
        return entry
