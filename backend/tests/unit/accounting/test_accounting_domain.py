from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

from davos.modules.accounting.domain.entities.account import Account
from davos.modules.accounting.domain.entities.fixed_asset import FixedAsset
from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.enums.revenue_recognition import RevenueRecognition
from davos.modules.accounting.domain.errors.account_not_postable_error import AccountNotPostableError
from davos.modules.accounting.domain.errors.empty_entry_error import EmptyEntryError
from davos.modules.accounting.domain.errors.entry_already_reversed_error import EntryAlreadyReversedError
from davos.modules.accounting.domain.errors.entry_not_reversible_error import EntryNotReversibleError
from davos.modules.accounting.domain.errors.invalid_line_error import InvalidLineError
from davos.modules.accounting.domain.errors.unbalanced_entry_error import UnbalancedEntryError
from davos.modules.accounting.domain.services.aging_calculator import AgingCalculator
from davos.modules.accounting.domain.services.default_chart import DEFAULT_CHART
from davos.modules.accounting.domain.services.depreciation_calculator import DepreciationCalculator
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.modules.accounting.domain.services.sales_posting_policy import SalesPostingPolicy
from davos.modules.accounting.domain.services.statement_builder import StatementBuilder
from davos.modules.accounting.domain.value_objects.account_balance import AccountBalance
from davos.modules.accounting.domain.value_objects.accounting_settings import AccountingSettings
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.modules.accounting.domain.value_objects.party_line import PartyLine
from davos.shared_kernel.domain.errors.validation_error import ValidationError

NOW = datetime(2026, 10, 14, 9, 0, tzinfo=UTC)
A, B = uuid.uuid4(), uuid.uuid4()


def entry(lines: list[JournalLine], source: EntrySource = EntrySource.MANUAL) -> JournalEntry:
    return JournalEntry.post(
        fiscal_year=1405,
        number=1,
        entry_date=date(2026, 10, 14),
        description="x",
        lines=lines,
        source=source,
        created_by="t",
        now=NOW,
    )


def roles() -> dict[AccountRole, uuid.UUID]:
    return {role: uuid.uuid4() for role in AccountRole}


# ---------------------------------------------------------------- lines and entries


@pytest.mark.parametrize(
    "kwargs",
    [{"debit_irr": 0, "credit_irr": 0}, {"debit_irr": 5, "credit_irr": 5}, {"debit_irr": -1}, {"credit_irr": True}],
)
def test_a_line_has_exactly_one_positive_side(kwargs: dict[str, object]) -> None:
    with pytest.raises(InvalidLineError):
        JournalLine(A, **kwargs)  # type: ignore[arg-type]


def test_an_entry_must_balance_and_have_two_lines() -> None:
    with pytest.raises(UnbalancedEntryError):
        entry([JournalLine(A, debit_irr=100), JournalLine(B, credit_irr=90)])
    with pytest.raises(EmptyEntryError):
        entry([JournalLine(A, debit_irr=100)])
    assert entry([JournalLine(A, debit_irr=100), JournalLine(B, credit_irr=100)]).total_irr == 100


def test_a_reversal_swaps_every_line_and_cancels_the_entry() -> None:
    original = entry([JournalLine(A, debit_irr=100, memo="m"), JournalLine(B, credit_irr=100)])
    swapped = original.reversal_lines()
    assert [(line.debit_irr, line.credit_irr) for line in swapped] == [(0, 100), (100, 0)]
    original.mark_reversed(uuid.uuid4())
    with pytest.raises(EntryAlreadyReversedError):
        original.reversal_lines()


def test_a_reversal_or_a_year_closing_cannot_itself_be_reversed() -> None:
    lines = [JournalLine(A, debit_irr=1), JournalLine(B, credit_irr=1)]
    for source in (EntrySource.REVERSAL, EntrySource.CLOSING):
        with pytest.raises(EntryNotReversibleError):
            entry(lines, source).reversal_lines()


# ---------------------------------------------------------------- the chart


def test_the_default_chart_is_consistent() -> None:
    codes = [t.code for t in DEFAULT_CHART]
    assert len(codes) == len(set(codes))
    by_code = {t.code: t for t in DEFAULT_CHART}
    for t in DEFAULT_CHART:
        if t.parent_code:
            parent = by_code[t.parent_code]
            assert parent.is_group and parent.account_type is t.account_type
    roles_used = [t.role for t in DEFAULT_CHART if t.role]
    assert len(roles_used) == len(set(roles_used)) and set(roles_used) == set(AccountRole)
    assert all(t.role is None or not t.is_group for t in DEFAULT_CHART)


def test_group_and_inactive_accounts_take_no_entries() -> None:
    group = Account.create(
        code="9", name="گروه", account_type=AccountType.ASSET, parent_id=None, is_group=True, now=NOW
    )
    leaf = Account.create(
        code="91", name="برگ", account_type=AccountType.ASSET, parent_id=group.id, is_group=False, now=NOW
    )
    with pytest.raises(AccountNotPostableError):
        group.ensure_postable()
    leaf.ensure_postable()
    leaf.edit(code="91", name="برگ", active=False)
    with pytest.raises(AccountNotPostableError):
        leaf.ensure_postable()


def test_a_bad_account_code_is_refused() -> None:
    with pytest.raises(ValidationError):
        Account.create(code="  ", name="x", account_type=AccountType.ASSET, parent_id=None, is_group=False, now=NOW)


# ---------------------------------------------------------------- the Jalali fiscal calendar


def test_fiscal_years_and_months_follow_the_jalali_calendar() -> None:
    assert FiscalCalendar.year_start(1405) == date(2026, 3, 21)
    assert FiscalCalendar.year_end(1405) == date(2027, 3, 20)
    assert FiscalCalendar.year_of(date(2026, 10, 14)) == 1405
    assert FiscalCalendar.month_of(date(2026, 10, 14)) == (1405, 7)
    assert FiscalCalendar.month_start(1405, 7) == date(2026, 9, 23)
    assert FiscalCalendar.month_end(1405, 7) == date(2026, 10, 22)
    assert FiscalCalendar.month_end(1405, 12) == FiscalCalendar.year_end(1405)
    assert FiscalCalendar.month_key(1405, 7) == "1405-07"


def test_every_month_starts_the_day_after_the_previous_one_ends() -> None:
    for year in (1403, 1404, 1405, 1406):
        for month in range(1, 12):
            assert (FiscalCalendar.month_end(year, month) - FiscalCalendar.month_start(year, month)).days in (
                28,
                29,
                30,
            )
            assert (
                FiscalCalendar.month_start(year, month + 1).toordinal()
                == FiscalCalendar.month_end(year, month).toordinal() + 1
            )


# ---------------------------------------------------------------- selling tickets


def test_vat_is_carved_out_of_the_price_not_added_on_top() -> None:
    assert SalesPostingPolicy.vat_part(1_100_000, 10) == 100_000
    assert SalesPostingPolicy.vat_part(1_000_000, 0) == 0


def test_an_online_sale_books_receipt_revenue_vat_and_the_gateway_fee() -> None:
    r = roles()
    settings = AccountingSettings(vat_percent=10, gateway_fee_bp=100)
    lines = SalesPostingPolicy.sale_lines(
        gross_irr=1_100_000,
        receipt_account_id=r[AccountRole.GATEWAY],
        roles=r,
        settings=settings,
        online=True,
        memo="m",
    )
    assert sum(line.debit_irr for line in lines) == sum(line.credit_irr for line in lines)
    by_account = {}
    for line in lines:
        by_account.setdefault(line.account_id, 0)
        by_account[line.account_id] += line.debit_irr - line.credit_irr
    assert by_account[r[AccountRole.SALES_REVENUE]] == -1_000_000
    assert by_account[r[AccountRole.VAT_PAYABLE]] == -100_000
    assert by_account[r[AccountRole.GATEWAY_FEES]] == 11_000
    assert by_account[r[AccountRole.GATEWAY]] == 1_100_000 - 11_000


def test_a_counter_sale_pays_no_gateway_fee_and_defers_revenue_when_asked() -> None:
    r = roles()
    lines = SalesPostingPolicy.sale_lines(
        gross_irr=500_000,
        receipt_account_id=r[AccountRole.CASH],
        roles=r,
        settings=AccountingSettings(gateway_fee_bp=200, revenue_recognition=RevenueRecognition.ON_SESSION),
        online=False,
        memo="m",
    )
    accounts = {line.account_id for line in lines}
    assert accounts == {r[AccountRole.CASH], r[AccountRole.DEFERRED_REVENUE]}


def test_earning_a_deferred_ticket_and_refunding_it() -> None:
    r = roles()
    settings = AccountingSettings(vat_percent=10, revenue_recognition=RevenueRecognition.ON_SESSION)
    sale = entry(
        SalesPostingPolicy.sale_lines(
            gross_irr=1_100_000,
            receipt_account_id=r[AccountRole.GATEWAY],
            roles=r,
            settings=settings,
            online=True,
            memo="m",
        ),
        EntrySource.ONLINE_SALE,
    )
    assert SalesPostingPolicy.deferred_amount(sale, r) == 1_000_000
    earning = SalesPostingPolicy.recognition_lines(sale, r, "m")
    assert [(line.account_id, line.debit_irr, line.credit_irr) for line in earning] == [
        (r[AccountRole.DEFERRED_REVENUE], 1_000_000, 0),
        (r[AccountRole.SALES_REVENUE], 0, 1_000_000),
    ]
    # refunded before the session: the advance and the VAT are undone, the customer is owed everything
    before = SalesPostingPolicy.refund_lines(
        sale, roles=r, recognized=False, credit_account_id=r[AccountRole.REFUNDS_PAYABLE], memo="m"
    )
    assert sum(line.debit_irr for line in before) == sum(line.credit_irr for line in before) == 1_100_000
    assert {line.account_id for line in before if line.debit_irr} == {
        r[AccountRole.DEFERRED_REVENUE],
        r[AccountRole.VAT_PAYABLE],
    }
    # refunded after the revenue was earned: it goes through sales returns instead
    after = SalesPostingPolicy.refund_lines(
        sale, roles=r, recognized=True, credit_account_id=r[AccountRole.REFUNDS_PAYABLE], memo="m"
    )
    assert r[AccountRole.SALES_RETURNS] in {line.account_id for line in after}


def test_invalid_accounting_settings_are_refused() -> None:
    for bad in ({"vat_percent": 31}, {"vat_percent": -1}, {"gateway_fee_bp": 1001}):
        with pytest.raises(ValidationError):
            AccountingSettings(**bad)


# ---------------------------------------------------------------- assets


def asset(**changes: object) -> FixedAsset:
    base = {
        "name": "کارت ۱",
        "asset_account_id": A,
        "cost_irr": 1_000_000,
        "salvage_irr": 100_000,
        "in_service_date": date(2026, 9, 25),
        "life_months": 3,
        "note": "",
        "now": NOW,
    }
    return FixedAsset.register(**{**base, **changes})  # type: ignore[arg-type]


def test_depreciation_is_even_and_the_last_month_takes_the_remainder() -> None:
    a = asset()  # 900_000 over 3 months, in service in Mehr 1405 (month 7)
    done = 0
    amounts = []
    for month in (6, 7, 8, 9, 10):
        amount = DepreciationCalculator.amount_for_month(a, 1405, month, done)
        amounts.append(amount)
        done += amount
    assert amounts == [0, 300_000, 300_000, 300_000, 0] and done == a.depreciable_irr


def test_rounding_never_loses_a_rial_of_depreciation() -> None:
    a = asset(cost_irr=1_000_001, salvage_irr=0, life_months=7)
    done = 0
    for month in range(7, 14):
        year, m = (1405, month) if month <= 12 else (1406, month - 12)
        done += DepreciationCalculator.amount_for_month(a, year, m, done)
    assert done == 1_000_001


def test_an_asset_needs_sensible_numbers() -> None:
    for bad in ({"cost_irr": 0}, {"salvage_irr": 2_000_000}, {"life_months": 0}, {"name": " "}):
        with pytest.raises(ValidationError):
            asset(**bad)


# ---------------------------------------------------------------- supplier ageing


def test_payments_settle_the_oldest_bill_first() -> None:
    v = uuid.uuid4()
    lines = [
        PartyLine(v, date(2026, 7, 1), 0, 100),  # old bill
        PartyLine(v, date(2026, 9, 20), 0, 50),  # newer bill
        PartyLine(v, date(2026, 9, 25), 120, 0),  # a payment: clears the old bill and part of the newer one
    ]
    [balance] = AgingCalculator.age(lines, date(2026, 10, 14))
    assert balance.owed_irr == 30 and balance.age_0_30 == 30 and balance.age_over_90 == 0 and balance.advance_irr == 0


def test_an_overpayment_is_an_advance_and_old_debts_are_aged() -> None:
    v, w = uuid.uuid4(), uuid.uuid4()
    lines = [
        PartyLine(v, date(2026, 1, 1), 0, 100),
        PartyLine(w, date(2026, 10, 1), 0, 10),
        PartyLine(w, date(2026, 10, 2), 25, 0),
    ]
    result = {b.party_id: b for b in AgingCalculator.age(lines, date(2026, 10, 14))}
    assert result[v].age_over_90 == 100 and result[v].owed_irr == 100
    assert result[w].owed_irr == 0 and result[w].advance_irr == 15


# ---------------------------------------------------------------- statements


def test_statements_agree_with_the_ledger() -> None:
    cash = Account.create(
        code="1101", name="صندوق", account_type=AccountType.ASSET, parent_id=None, is_group=False, now=NOW
    )
    sales = Account.create(
        code="4101", name="فروش", account_type=AccountType.REVENUE, parent_id=None, is_group=False, now=NOW
    )
    fuel = Account.create(
        code="5101", name="سوخت", account_type=AccountType.EXPENSE, parent_id=None, is_group=False, now=NOW
    )
    capital = Account.create(
        code="3101", name="سرمایه", account_type=AccountType.EQUITY, parent_id=None, is_group=False, now=NOW
    )
    accounts = [cash, sales, fuel, capital]
    # capital 1000 in, sales 500 in cash, fuel 200 out of cash
    balances = [
        AccountBalance(cash.id, 0, 1500, 200),
        AccountBalance(capital.id, 0, 0, 1000),
        AccountBalance(sales.id, 0, 0, 500),
        AccountBalance(fuel.id, 0, 200, 0),
    ]
    income = StatementBuilder.income_statement(accounts, balances, date(2026, 9, 23), date(2026, 10, 22))
    assert (income.total_revenue, income.total_expenses, income.net_profit) == (500, 200, 300)
    sheet = StatementBuilder.balance_sheet(accounts, balances, date(2026, 10, 22))
    assert sheet.total_assets == 1300 and sheet.total_equity == 1300 and sheet.current_earnings_irr == 300
    assert sheet.difference_irr == 0
    trial = StatementBuilder.trial_balance(accounts, balances)
    assert sum(r.closing_debit for r in trial) == sum(r.closing_credit for r in trial)
