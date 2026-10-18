from __future__ import annotations

import uuid

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.budget_repository import BudgetRepository
from davos.modules.accounting.application.ports.ledger_query import LedgerQuery
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.errors.account_not_found_error import AccountNotFoundError
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.modules.accounting.domain.value_objects.budget_row import BudgetRow
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.validation_error import ValidationError


class BudgetUseCase:
    """A monthly budget per revenue or expense account, compared with what the books actually show."""

    def __init__(
        self, *, uow: UnitOfWork, budgets: BudgetRepository, accounts: AccountRepository, ledger: LedgerQuery
    ) -> None:
        self._uow = uow
        self._budgets = budgets
        self._accounts = accounts
        self._ledger = ledger

    async def set_month(self, account_id: uuid.UUID, year: int, month: int, amount_irr: int) -> None:
        if not 1 <= month <= 12 or amount_irr < 0:
            raise ValidationError("ماه یا مبلغ بودجه معتبر نیست.", code="invalid_budget")
        async with self._uow:
            account = await self._accounts.get(account_id)
            if account is None:
                raise AccountNotFoundError
            if not account.type.is_temporary or account.is_group:
                raise ValidationError("بودجه فقط برای حساب‌های درآمد و هزینه ثبت می‌شود.", code="budget_account_type")
            await self._budgets.set_amount(account_id, year, month, amount_irr)
            await self._uow.commit()

    async def set_whole_year(self, account_id: uuid.UUID, year: int, yearly_irr: int) -> None:
        """Spreads a yearly figure evenly over the twelve months (the remainder goes to the last month)."""
        base, rest = divmod(max(yearly_irr, 0), 12)
        for month in range(1, 13):
            await self.set_month(account_id, year, month, base + (rest if month == 12 else 0))

    async def report(self, year: int, month_from: int, month_to: int) -> list[BudgetRow]:
        if not 1 <= month_from <= month_to <= 12:
            raise ValidationError("بازه ماه‌ها معتبر نیست.", code="invalid_months")
        date_from = FiscalCalendar.month_start(year, month_from)
        date_to = FiscalCalendar.month_end(year, month_to)
        async with self._uow:
            accounts = {a.id: a for a in await self._accounts.list_all()}
            budget = await self._budgets.for_year(year)
            balances = await self._ledger.balances(date_from, date_to, [EntrySource.CLOSING])
        actual = {b.account_id: b for b in balances}
        planned: dict[uuid.UUID, int] = {}
        for (account_id, month), amount in budget.items():
            if month_from <= month <= month_to:
                planned[account_id] = planned.get(account_id, 0) + amount
        rows: list[BudgetRow] = []
        for account_id in sorted(
            set(planned)
            | {
                a
                for a, b in actual.items()
                if accounts.get(a) and accounts[a].type.is_temporary and (b.debit or b.credit)
            }
        ):
            account = accounts.get(account_id)
            if account is None or not account.type.is_temporary:
                continue
            movement = actual.get(account_id)
            amount = 0
            if movement is not None:
                amount = (
                    movement.credit - movement.debit
                    if account.type is AccountType.REVENUE
                    else movement.debit - movement.credit
                )
            rows.append(
                BudgetRow(
                    account_id, account.code, account.name, account.type.value, planned.get(account_id, 0), amount
                )
            )
        return sorted(rows, key=lambda r: r.code)
