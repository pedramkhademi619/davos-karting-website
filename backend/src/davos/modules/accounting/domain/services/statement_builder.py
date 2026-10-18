from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from datetime import date

from davos.modules.accounting.domain.entities.account import Account
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.value_objects.account_balance import AccountBalance
from davos.modules.accounting.domain.value_objects.balance_sheet import BalanceSheet
from davos.modules.accounting.domain.value_objects.income_statement import IncomeStatement
from davos.modules.accounting.domain.value_objects.statement_line import StatementLine
from davos.modules.accounting.domain.value_objects.trial_balance_row import TrialBalanceRow


class StatementBuilder:
    """Turns account movements into the standard statements. Pure arithmetic over what the ledger reports."""

    @staticmethod
    def _index(accounts: Sequence[Account]) -> Mapping[uuid.UUID, Account]:
        return {a.id: a for a in accounts}

    @staticmethod
    def _group_name(account: Account, by_id: Mapping[uuid.UUID, Account]) -> str:
        parent = by_id.get(account.parent_id) if account.parent_id else None
        return parent.name if parent else ""

    @classmethod
    def trial_balance(cls, accounts: Sequence[Account], balances: Sequence[AccountBalance]) -> list[TrialBalanceRow]:
        by_id = cls._index(accounts)
        rows: list[TrialBalanceRow] = []
        for b in balances:
            account = by_id.get(b.account_id)
            if account is None or not (b.opening_net or b.debit or b.credit):
                continue
            rows.append(
                TrialBalanceRow(
                    account_id=account.id,
                    code=account.code,
                    name=account.name,
                    account_type=account.type.value,
                    opening_debit=max(b.opening_net, 0),
                    opening_credit=max(-b.opening_net, 0),
                    debit=b.debit,
                    credit=b.credit,
                    closing_debit=max(b.closing_net, 0),
                    closing_credit=max(-b.closing_net, 0),
                )
            )
        return sorted(rows, key=lambda r: r.code)

    @classmethod
    def income_statement(
        cls, accounts: Sequence[Account], balances: Sequence[AccountBalance], date_from: date, date_to: date
    ) -> IncomeStatement:
        by_id = cls._index(accounts)
        revenue: list[StatementLine] = []
        expenses: list[StatementLine] = []
        for b in balances:
            account = by_id.get(b.account_id)
            if account is None or account.type not in (AccountType.REVENUE, AccountType.EXPENSE):
                continue
            amount = b.credit - b.debit if account.type is AccountType.REVENUE else b.debit - b.credit
            if amount == 0:
                continue
            line = StatementLine(account.id, account.code, account.name, cls._group_name(account, by_id), amount)
            (revenue if account.type is AccountType.REVENUE else expenses).append(line)
        key = lambda line: line.code  # noqa: E731
        return IncomeStatement(date_from, date_to, tuple(sorted(revenue, key=key)), tuple(sorted(expenses, key=key)))

    @classmethod
    def balance_sheet(
        cls, accounts: Sequence[Account], balances: Sequence[AccountBalance], as_of: date
    ) -> BalanceSheet:
        by_id = cls._index(accounts)
        sections: dict[AccountType, list[StatementLine]] = {t: [] for t in AccountType}
        earnings = 0
        for b in balances:
            account = by_id.get(b.account_id)
            if account is None:
                continue
            net = b.closing_net
            if account.type.is_temporary:
                earnings -= net  # revenue is credit-heavy (negative net), so profit = -(sum of temporary nets)
                continue
            if net == 0:
                continue
            amount = net if account.type.debit_normal else -net
            sections[account.type].append(
                StatementLine(account.id, account.code, account.name, cls._group_name(account, by_id), amount)
            )
        key = lambda line: line.code  # noqa: E731
        return BalanceSheet(
            as_of=as_of,
            assets=tuple(sorted(sections[AccountType.ASSET], key=key)),
            liabilities=tuple(sorted(sections[AccountType.LIABILITY], key=key)),
            equity=tuple(sorted(sections[AccountType.EQUITY], key=key)),
            current_earnings_irr=earnings,
        )
