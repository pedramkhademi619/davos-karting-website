from __future__ import annotations

import uuid
from datetime import date

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.cash_closing_repository import CashClosingRepository
from davos.modules.accounting.application.ports.journal_repository import JournalRepository
from davos.modules.accounting.application.ports.ledger_query import LedgerQuery
from davos.modules.accounting.application.services.ledger_posting_service import LedgerPostingService
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.errors.cash_day_already_closed_error import CashDayAlreadyClosedError
from davos.modules.accounting.domain.errors.invalid_amount_error import InvalidAmountError
from davos.modules.accounting.domain.errors.missing_system_account_error import MissingSystemAccountError
from davos.modules.accounting.domain.value_objects.cash_closing import CashClosing
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class CashClosingUseCase:
    """The end-of-day count of the till: the books say what it should hold; a difference is booked as such."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        closings: CashClosingRepository,
        accounts: AccountRepository,
        journal: JournalRepository,
        ledger: LedgerQuery,
        posting: LedgerPostingService,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._closings = closings
        self._accounts = accounts
        self._journal = journal
        self._ledger = ledger
        self._posting = posting
        self._clock = clock

    async def _expected(self, day: date) -> tuple[int, uuid.UUID]:
        cash = (await self._accounts.roles()).get(AccountRole.CASH)
        if cash is None:
            raise MissingSystemAccountError
        balances = await self._ledger.balances(None, day)
        return next((b.closing_net for b in balances if b.account_id == cash), 0), cash

    async def expected_cash(self, day: date) -> int:
        async with self._uow:
            return (await self._expected(day))[0]

    async def recent(self, limit: int = 30) -> list[CashClosing]:
        async with self._uow:
            return await self._closings.recent(limit)

    async def close_day(self, day: date, *, counted_irr: int, note: str, closed_by: str) -> CashClosing:
        if counted_irr < 0:
            raise InvalidAmountError("مبلغ شمارش‌شده نمی‌تواند منفی باشد.")
        async with self._uow:
            await self._journal.lock_ledger()
            if await self._closings.get(day) is not None:
                raise CashDayAlreadyClosedError
            expected, cash = await self._expected(day)
            difference = counted_irr - expected
            entry_id = None
            if difference:
                roles = await self._accounts.roles()
                gap = roles.get(AccountRole.CASH_DIFFERENCE)
                if gap is None:
                    raise MissingSystemAccountError
                memo = f"{'اضافه' if difference > 0 else 'کسری'} صندوق {day.isoformat()}"
                lines = (
                    [
                        JournalLine(cash, debit_irr=difference, memo=memo),
                        JournalLine(gap, credit_irr=difference, memo=memo),
                    ]
                    if difference > 0
                    else [
                        JournalLine(gap, debit_irr=-difference, memo=memo),
                        JournalLine(cash, credit_irr=-difference, memo=memo),
                    ]
                )
                entry = await self._posting.post(
                    entry_date=day,
                    description=memo,
                    lines=lines,
                    source=EntrySource.CASH_CLOSE,
                    source_ref=day.isoformat(),
                    created_by=closed_by,
                )
                entry_id = entry.id
            closing = CashClosing(
                closing_id=uuid.uuid4(),
                day=day,
                expected_irr=expected,
                counted_irr=counted_irr,
                entry_id=entry_id,
                note=note.strip()[:300],
                closed_by=closed_by,
                created_at=self._clock.now(),
            )
            await self._closings.add(closing)
            await self._uow.commit()
        return closing
