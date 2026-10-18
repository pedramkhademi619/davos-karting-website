from __future__ import annotations

from datetime import date

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.accounting_settings_repository import AccountingSettingsRepository
from davos.modules.accounting.application.ports.journal_repository import JournalRepository
from davos.modules.accounting.application.services.ledger_posting_service import LedgerPostingService
from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.errors.missing_system_account_error import MissingSystemAccountError
from davos.modules.accounting.domain.errors.period_locked_error import PeriodLockedError
from davos.modules.accounting.domain.services.sales_posting_policy import SalesPostingPolicy
from davos.modules.accounting.domain.services.tehran_calendar import TehranCalendar
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork

# Card-reader and online (Shaparak) payments are settled into the bank account by the payment network itself, so they
# are booked straight to the bank: nobody has to move "card reader" or "gateway" balances to the bank by hand.
_COUNTER_ACCOUNT_ROLE = {"cash": AccountRole.CASH, "card": AccountRole.BANK, "transfer": AccountRole.BANK}
_SYSTEM = "system"
_RECOGNITION_BATCH = 500


class SalesPostingUseCase:
    """Books tickets from reservation events: a paid online ticket, a counter sale, the earning of a ticket when its
    session day comes, and the refund of a cancelled one. Each is posted at most once per reservation."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        accounts: AccountRepository,
        journal: JournalRepository,
        settings: AccountingSettingsRepository,
        posting: LedgerPostingService,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._accounts = accounts
        self._journal = journal
        self._settings = settings
        self._posting = posting
        self._clock = clock

    async def post_sale(
        self,
        *,
        reservation_id: str,
        amount_irr: int,
        online: bool,
        counter_method: str | None,
        session_day: date,
        label: str,
    ) -> bool:
        """True when the sale was booked now; False when it was already booked or is not booked at all.

        ``counter_method`` is cash, card or transfer for a counter sale; anything else (free, pay later) is not booked.
        """
        if amount_irr <= 0:
            return False
        source = EntrySource.ONLINE_SALE if online else EntrySource.COUNTER_SALE
        role = AccountRole.BANK if online else _COUNTER_ACCOUNT_ROLE.get(counter_method or "")
        if role is None:
            return False
        async with self._uow:
            settings = await self._settings.get()
            if not settings.auto_posting_enabled:
                return False
            await self._journal.lock_ledger()
            if await self._journal.find_by_source(source, reservation_id) is not None:
                return False
            roles = await self._accounts.roles()
            if role not in roles:
                raise MissingSystemAccountError
            lines = SalesPostingPolicy.sale_lines(
                gross_irr=amount_irr,
                receipt_account_id=roles[role],
                roles=roles,
                settings=settings,
                online=online,
                memo=label,
            )
            await self._posting.post(
                entry_date=TehranCalendar.today(self._clock.now()),
                description=label,
                lines=lines,
                source=source,
                source_ref=reservation_id,
                source_date=session_day,
                created_by=_SYSTEM,
            )
            await self._uow.commit()
        return True

    async def refund_sale(self, *, reservation_id: str, label: str) -> JournalEntry | None:
        """A cancelled ticket: online money becomes a debt to the customer; a counter sale is paid back in cash."""
        async with self._uow:
            settings = await self._settings.get()
            if not settings.auto_posting_enabled:
                return None
            await self._journal.lock_ledger()
            sale = await self._journal.find_by_source(EntrySource.ONLINE_SALE, reservation_id)
            online = sale is not None
            if sale is None:
                sale = await self._journal.find_by_source(EntrySource.COUNTER_SALE, reservation_id)
            if sale is None:
                return None
            existing = await self._journal.find_by_source(EntrySource.REFUND, reservation_id)
            if existing is not None:
                return existing
            roles = await self._accounts.roles()
            recognized = await self._journal.find_by_source(EntrySource.RECOGNITION, reservation_id) is not None
            if online:
                credit_account = roles[AccountRole.REFUNDS_PAYABLE]
            else:
                receipt = next(line for line in sale.lines if line.debit_irr > 0)
                credit_account = receipt.account_id
            lines = SalesPostingPolicy.refund_lines(
                sale, roles=roles, recognized=recognized, credit_account_id=credit_account, memo=label
            )
            entry = await self._posting.post(
                entry_date=TehranCalendar.today(self._clock.now()),
                description=label,
                lines=lines,
                source=EntrySource.REFUND,
                source_ref=reservation_id,
                source_date=sale.source_date,
                created_by=_SYSTEM,
            )
            await self._uow.commit()
        return entry

    async def recognize_due(self) -> int:
        """Moves ticket money from "customer advances" to revenue once the session day has come (accrual mode)."""
        today = TehranCalendar.today(self._clock.now())
        done = 0
        async with self._uow:
            settings = await self._settings.get()
            await self._journal.lock_ledger()
            roles = await self._accounts.roles()
            for sale in await self._journal.unrecognized_sales(today, _RECOGNITION_BATCH):
                if sale.source_ref is None or sale.source_date is None:  # every sale entry carries both
                    continue
                locked = settings.locked_through is not None and sale.source_date <= settings.locked_through
                try:
                    await self._posting.post(
                        entry_date=today if locked else sale.source_date,
                        description=f"شناسایی درآمد: {sale.description}",
                        lines=SalesPostingPolicy.recognition_lines(sale, roles, f"شناسایی درآمد {sale.description}"),
                        source=EntrySource.RECOGNITION,
                        source_ref=sale.source_ref,
                        source_date=sale.source_date,
                        created_by=_SYSTEM,
                    )
                except PeriodLockedError:
                    continue
                done += 1
            await self._uow.commit()
        return done
