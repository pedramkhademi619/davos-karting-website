from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta

from davos.modules.accounting.application.ports.account_ledger import AccountLedger
from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.journal_repository import JournalRepository
from davos.modules.accounting.application.ports.ledger_query import LedgerQuery
from davos.modules.accounting.domain.entities.account import Account
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.errors.account_not_found_error import AccountNotFoundError
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.modules.accounting.domain.services.statement_builder import StatementBuilder
from davos.modules.accounting.domain.services.tehran_calendar import TehranCalendar
from davos.modules.accounting.domain.value_objects.accounting_dashboard import AccountingDashboard
from davos.modules.accounting.domain.value_objects.balance_sheet import BalanceSheet
from davos.modules.accounting.domain.value_objects.income_statement import IncomeStatement
from davos.modules.accounting.domain.value_objects.monthly_point import MonthlyPoint
from davos.modules.accounting.domain.value_objects.sales_summary import SalesSummary
from davos.modules.accounting.domain.value_objects.sales_summary_day import SalesSummaryDay
from davos.modules.accounting.domain.value_objects.statement_line import StatementLine
from davos.modules.accounting.domain.value_objects.trial_balance_row import TrialBalanceRow
from davos.modules.accounting.domain.value_objects.vat_report import VatReport
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.validation_error import ValidationError

_CASH_ROLES = (AccountRole.CASH, AccountRole.BANK, AccountRole.POS, AccountRole.GATEWAY)


def _channel(source: str, role: str) -> str:
    """Online tickets, counter cash (the till), or counter card/transfer (the bank). Online and card money used to sit
    in gateway and card-reader accounts and now goes straight to the bank, so the entry's source decides "online"."""
    if source == "online_sale":
        return "online"
    return "cash" if role == "cash" else "card"


class AccountingReportsUseCase:
    """Every report is computed from the posted journal lines, so reports can never disagree with the books."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        accounts: AccountRepository,
        journal: JournalRepository,
        ledger: LedgerQuery,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._accounts = accounts
        self._journal = journal
        self._ledger = ledger
        self._clock = clock

    @staticmethod
    def _check_range(date_from: date, date_to: date) -> None:
        if date_from > date_to or (date_to - date_from).days > 3700:
            raise ValidationError("بازه تاریخ معتبر نیست.", code="invalid_range")

    async def trial_balance(self, date_from: date, date_to: date) -> list[TrialBalanceRow]:
        self._check_range(date_from, date_to)
        async with self._uow:
            accounts = await self._accounts.list_all()
            balances = await self._ledger.balances(date_from, date_to)
        return StatementBuilder.trial_balance(accounts, balances)

    async def general_ledger(
        self, account_id: uuid.UUID, date_from: date, date_to: date
    ) -> tuple[Account, AccountLedger]:
        self._check_range(date_from, date_to)
        async with self._uow:
            accounts = await self._accounts.list_all()
            account = next((a for a in accounts if a.id == account_id), None)
            if account is None:
                raise AccountNotFoundError
            ids = {account.id}
            grew = True
            while grew:
                children = {a.id for a in accounts if a.parent_id in ids} - ids
                grew = bool(children)
                ids |= children
            return account, await self._ledger.account_ledger(ids, date_from, date_to)

    async def income_statement(self, date_from: date, date_to: date) -> tuple[IncomeStatement, IncomeStatement]:
        """The period and the equally long period just before it, for comparison."""
        self._check_range(date_from, date_to)
        length = (date_to - date_from).days + 1
        previous_to = date_from - timedelta(days=1)
        previous_from = previous_to - timedelta(days=length - 1)
        async with self._uow:
            accounts = await self._accounts.list_all()
            now = await self._ledger.balances(date_from, date_to, [EntrySource.CLOSING])
            before = await self._ledger.balances(previous_from, previous_to, [EntrySource.CLOSING])
        return (
            StatementBuilder.income_statement(accounts, now, date_from, date_to),
            StatementBuilder.income_statement(accounts, before, previous_from, previous_to),
        )

    async def balance_sheet(self, as_of: date) -> BalanceSheet:
        async with self._uow:
            accounts = await self._accounts.list_all()
            balances = await self._ledger.balances(None, as_of)
        return StatementBuilder.balance_sheet(accounts, balances, as_of)

    async def sales_summary(self, date_from: date, date_to: date) -> SalesSummary:
        self._check_range(date_from, date_to)
        async with self._uow:
            receipts = await self._ledger.sales_receipts(date_from, date_to)
            revenue = await self._ledger.revenue_by_day(date_from, date_to)
        by_day: dict[date, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in receipts:
            by_day[r.day][_channel(r.source, r.role)] += r.amount_irr
        for item in revenue:
            by_day[item.day]["revenue"] += item.amount_irr
        days = tuple(
            SalesSummaryDay(
                day=day,
                online_irr=v["online"],
                cash_irr=v["cash"],
                card_irr=v["card"],
                revenue_irr=v["revenue"],
            )
            for day, v in sorted(by_day.items())
        )
        return SalesSummary(days)

    async def vat_report(self, date_from: date, date_to: date) -> VatReport:
        self._check_range(date_from, date_to)
        async with self._uow:
            roles = await self._accounts.roles()
            balances = {b.account_id: b for b in await self._ledger.balances(date_from, date_to)}
        payable = balances.get(roles.get(AccountRole.VAT_PAYABLE, uuid.UUID(int=0)))
        receivable = balances.get(roles.get(AccountRole.VAT_RECEIVABLE, uuid.UUID(int=0)))
        collected = (payable.credit - payable.debit) if payable else 0
        paid = (receivable.debit - receivable.credit) if receivable else 0
        opening = (-(payable.opening_net) if payable else 0) - (receivable.opening_net if receivable else 0)
        return VatReport(collected, paid, opening)

    async def cash_position(self, as_of: date) -> list[StatementLine]:
        async with self._uow:
            accounts = {a.id: a for a in await self._accounts.list_all()}
            balances = await self._ledger.balances(None, as_of)
        lines: list[StatementLine] = []
        for b in balances:
            account = accounts.get(b.account_id)
            if account is None or account.role not in _CASH_ROLES:
                continue
            lines.append(StatementLine(account.id, account.code, account.name, account.role.value, b.closing_net))
        return sorted(lines, key=lambda line: line.code)

    async def dashboard(self) -> AccountingDashboard:
        today = TehranCalendar.today(self._clock.now())
        year, month = FiscalCalendar.month_of(today)
        month_from, month_to = FiscalCalendar.month_start(year, month), FiscalCalendar.month_end(year, month)
        async with self._uow:
            accounts = await self._accounts.list_all()
            roles = await self._accounts.roles()
            balances = {b.account_id: b for b in await self._ledger.balances(None, today)}
            month_balances = await self._ledger.balances(month_from, month_to, [EntrySource.CLOSING])
            today_revenue = sum(r.amount_irr for r in await self._ledger.revenue_by_day(today, today))
            trend: list[MonthlyPoint] = []
            for back in range(5, -1, -1):
                index = year * 12 + (month - 1) - back
                ty, tm = index // 12, index % 12 + 1
                start, end = FiscalCalendar.month_start(ty, tm), FiscalCalendar.month_end(ty, tm)
                statement = StatementBuilder.income_statement(
                    accounts, await self._ledger.balances(start, end, [EntrySource.CLOSING]), start, end
                )
                trend.append(
                    MonthlyPoint(FiscalCalendar.month_key(ty, tm), statement.total_revenue, statement.total_expenses)
                )

        def net(role: AccountRole) -> int:
            account_id = roles.get(role)
            found = balances.get(account_id) if account_id else None
            return found.closing_net if found else 0

        statement = StatementBuilder.income_statement(accounts, month_balances, month_from, month_to)
        return AccountingDashboard(
            cash_irr=net(AccountRole.CASH),
            bank_irr=net(AccountRole.BANK),
            pos_irr=net(AccountRole.POS),
            gateway_irr=net(AccountRole.GATEWAY),
            payables_irr=-net(AccountRole.PAYABLES),
            refunds_payable_irr=-net(AccountRole.REFUNDS_PAYABLE),
            vat_balance_irr=-net(AccountRole.VAT_PAYABLE) - net(AccountRole.VAT_RECEIVABLE),
            today_revenue_irr=today_revenue,
            month_revenue_irr=statement.total_revenue,
            month_expenses_irr=statement.total_expenses,
            unrecognized_advances_irr=-net(AccountRole.DEFERRED_REVENUE),
            trend=tuple(trend),
            top_expenses=tuple(sorted(statement.expenses, key=lambda line: -line.amount_irr)[:5]),
        )
