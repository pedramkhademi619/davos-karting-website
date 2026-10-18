"""The books end to end on real PostgreSQL: posting, the database's own protection of the ledger, automatic booking of
tickets from reservations, suppliers, assets, the till, the fiscal year and the owner-only API."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, time

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.api.app_factory import create_app
from davos.composition.accounting_events import AccountingEvents
from davos.composition.application_container import ApplicationContainer
from davos.modules.accounting.application.ports.journal_query import JournalQuery
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.enums.revenue_recognition import RevenueRecognition
from davos.modules.accounting.domain.errors.entry_already_reversed_error import EntryAlreadyReversedError
from davos.modules.accounting.domain.errors.period_locked_error import PeriodLockedError
from davos.modules.accounting.domain.errors.unbalanced_entry_error import UnbalancedEntryError
from davos.modules.accounting.domain.value_objects.accounting_settings import AccountingSettings
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.modules.assistant.adapters.budget.in_memory_ai_budget import InMemoryAiBudget
from davos.modules.notifications.adapters.sms.recording_sms_gateway import RecordingSmsGateway
from davos.modules.reservations.application.use_cases.staff_reservation_command import StaffReservationCommand
from davos.modules.reservations.domain.enums.counter_payment_method import CounterPaymentMethod
from davos.platform.rate_limiting.in_memory_rate_limiter import InMemoryRateLimiter
from davos.platform.settings.app_settings import AppSettings
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.scripted_ai_chat import ScriptedAiChat
from tests.fakes.scripted_payment_gateway import ScriptedPaymentGateway
from tests.integration.api.conftest import ORIGIN

pytestmark = pytest.mark.integration

OWNER_PASSWORD = "Owner-password-2026"
STAFF_PASSWORD = "Staff-password-2026"
NOW = datetime(2026, 10, 14, 9, 0, tzinfo=UTC)  # 12:30 in Tehran, 22 Mehr 1405
TODAY = date(2026, 10, 14)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
async def container(test_settings: AppSettings, engine: AsyncEngine, clock: FixedClock) -> ApplicationContainer:
    settings = test_settings.model_copy(
        update={"admin_bootstrap_username": "owner", "admin_bootstrap_password": OWNER_PASSWORD}
    )
    books = ApplicationContainer(
        settings=settings,
        engine=engine,
        redis=None,
        clock=clock,
        rate_limiter=InMemoryRateLimiter(clock),
        sms_gateway=RecordingSmsGateway(),
        ai_chat=ScriptedAiChat("x"),
        ai_budget=InMemoryAiBudget(daily_limit=1_000_000, clock=clock),
        payment_gateway=ScriptedPaymentGateway(),
    )
    await books.chart_of_accounts().seed_default()
    return books


async def role(container: ApplicationContainer, which: AccountRole) -> uuid.UUID:
    return (await _roles(container))[which]


async def _roles(container: ApplicationContainer) -> dict[AccountRole, uuid.UUID]:
    return {a.role: a.id for a in await container.chart_of_accounts().list_all() if a.role}


async def code(container: ApplicationContainer, account_code: str) -> uuid.UUID:
    return next(a.id for a in await container.chart_of_accounts().list_all() if a.code == account_code)


async def balance(container: ApplicationContainer, account_id: uuid.UUID, day: date = TODAY) -> int:
    rows = await container.accounting_reports().trial_balance(date(2026, 3, 21), day)
    return next((r.closing_debit - r.closing_credit for r in rows if r.account_id == account_id), 0)


async def counter_sale(
    container: ApplicationContainer, method: CounterPaymentMethod, amount: int = 790_000
) -> uuid.UUID:
    reservation = await container.create_staff_reservation().execute(
        StaffReservationCommand(
            day=date(2026, 10, 15),
            session_time=time(18, 0),
            single_count=1,
            double_count=0,
            contact_name="علی",
            contact_mobile="09120000000",
            note="",
            amount_irr=amount * 10,
            payment_method=method,
        )
    )
    return reservation.id


# ---------------------------------------------------------------- the chart


async def test_the_default_chart_is_created_once_and_every_system_job_has_an_account(
    container: ApplicationContainer,
) -> None:
    assert await container.chart_of_accounts().seed_default() == 0  # the fixture already seeded it
    assert set(await _roles(container)) == set(AccountRole)


async def test_system_accounts_can_be_renamed_but_not_removed_and_used_accounts_are_kept(
    container: ApplicationContainer,
) -> None:
    cash = await role(container, AccountRole.CASH)
    renamed = await container.chart_of_accounts().update(cash, code="1101", name="صندوق مرکزی", active=True)
    assert renamed.name == "صندوق مرکزی"
    with pytest.raises(Exception, match="سیستمی"):
        await container.chart_of_accounts().delete(cash)


# ---------------------------------------------------------------- posting and the database's own protection


async def post(container: ApplicationContainer, debit: uuid.UUID, credit: uuid.UUID, amount: int, day: date = TODAY):
    return await container.journal().post_manual(
        entry_date=day,
        description="دستی",
        lines=[JournalLine(debit, debit_irr=amount), JournalLine(credit, credit_irr=amount)],
        created_by="owner",
    )


async def test_entries_are_numbered_without_gaps_even_under_concurrency(container: ApplicationContainer) -> None:
    cash, capital = await role(container, AccountRole.CASH), await role(container, AccountRole.CAPITAL)
    entries = await asyncio.gather(*(post(container, cash, capital, 1000 + i) for i in range(12)))
    assert sorted(e.number for e in entries) == list(range(1, 13))
    assert {e.fiscal_year for e in entries} == {1405}


async def test_an_unbalanced_or_one_sided_entry_is_refused_before_it_reaches_the_database(
    container: ApplicationContainer,
) -> None:
    cash, capital = await role(container, AccountRole.CASH), await role(container, AccountRole.CAPITAL)
    with pytest.raises(UnbalancedEntryError):
        await container.journal().post_manual(
            entry_date=TODAY,
            description="x",
            lines=[JournalLine(cash, debit_irr=10), JournalLine(capital, credit_irr=9)],
            created_by="o",
        )


async def _insert_unbalanced_entry(engine: AsyncEngine, debit_account: uuid.UUID, credit_account: uuid.UUID) -> None:
    entry_id = uuid.uuid4()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO accounting_journal_entries"
                " (id, fiscal_year, number, entry_date, description, source, status, created_by, created_at)"
                " VALUES (:id, 1405, 900, :day, 'x', 'manual', 'posted', 'raw', now())"
            ),
            {"id": entry_id, "day": TODAY},
        )
        for line_no, (account, debit, credit) in enumerate(((debit_account, 100, 0), (credit_account, 0, 90)), start=1):
            await conn.execute(
                text(
                    "INSERT INTO accounting_journal_lines"
                    " (entry_id, line_no, account_id, debit_irr, credit_irr, memo) VALUES (:e, :n, :a, :d, :c, '')"
                ),
                {"e": entry_id, "n": line_no, "a": account, "d": debit, "c": credit},
            )


async def test_the_database_itself_refuses_an_unbalanced_entry_and_any_change_to_posted_lines(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    cash, capital = await role(container, AccountRole.CASH), await role(container, AccountRole.CAPITAL)
    entry = await post(container, cash, capital, 500)
    with pytest.raises(
        (IntegrityError, DBAPIError)
    ):  # debit 100 against credit 90, checked when the transaction commits
        await _insert_unbalanced_entry(engine, cash, capital)
    for statement in (
        "UPDATE accounting_journal_lines SET debit_irr = debit_irr + 1 WHERE entry_id = :e",
        "DELETE FROM accounting_journal_lines WHERE entry_id = :e",
        "DELETE FROM accounting_journal_entries WHERE id = :e",
        "UPDATE accounting_journal_entries SET description = 'edited' WHERE id = :e",
    ):
        with pytest.raises((IntegrityError, DBAPIError)):
            async with engine.begin() as conn:
                await conn.execute(text(statement), {"e": entry.id})


async def test_reversal_cancels_an_entry_exactly_and_only_once(container: ApplicationContainer) -> None:
    cash, capital = await role(container, AccountRole.CASH), await role(container, AccountRole.CAPITAL)
    entry = await post(container, cash, capital, 750)
    assert await balance(container, cash) == 750
    reversal = await container.journal().reverse(entry.id, reason="اشتباه", created_by="owner")
    assert reversal.source is EntrySource.REVERSAL and reversal.reversal_of_id == entry.id
    assert await balance(container, cash) == 0
    assert (await container.journal().get(entry.id)).status.value == "reversed"
    with pytest.raises(EntryAlreadyReversedError):
        await container.journal().reverse(entry.id, reason="دوباره", created_by="owner")


async def test_a_locked_period_refuses_new_entries(container: ApplicationContainer) -> None:
    cash, capital = await role(container, AccountRole.CASH), await role(container, AccountRole.CAPITAL)
    await container.accounting_settings().update(AccountingSettings(locked_through=date(2026, 10, 1)))
    with pytest.raises(PeriodLockedError):
        await post(container, cash, capital, 1, day=date(2026, 10, 1))
    await post(container, cash, capital, 1, day=date(2026, 10, 2))


# ---------------------------------------------------------------- tickets are booked from reservations


async def test_a_counter_sale_lands_in_the_right_account_once_and_a_cancellation_gives_it_back(
    container: ApplicationContainer,
) -> None:
    cash, bank = await role(container, AccountRole.CASH), await role(container, AccountRole.BANK)
    revenue = await role(container, AccountRole.SALES_REVENUE)
    events = AccountingEvents(container)
    sale_id = await counter_sale(container, CounterPaymentMethod.CASH, 790_000)
    card_id = await counter_sale(container, CounterPaymentMethod.CARD, 500_000)
    held_id = await counter_sale(container, CounterPaymentMethod.NONE, 100_000)
    for reservation_id in (sale_id, sale_id, card_id, held_id):  # the same event twice changes nothing
        await events.book_sale(reservation_id)
    assert await balance(container, cash) == 7_900_000
    assert await balance(container, bank) == 5_000_000  # the card network settles into the bank by itself
    assert await balance(container, revenue) == -12_900_000  # no entry for the seat held without money
    await events.book_refund(sale_id)
    await events.book_refund(sale_id)
    assert await balance(container, cash) == 0
    assert await balance(container, await role(container, AccountRole.SALES_RETURNS)) == 7_900_000


async def test_vat_and_the_gateway_fee_are_booked_for_an_online_sale_and_refunds_become_a_debt(
    container: ApplicationContainer,
) -> None:
    await container.accounting_settings().update(AccountingSettings(vat_percent=10, gateway_fee_bp=100))
    assert await container.sales_posting().post_sale(
        reservation_id="r-1",
        amount_irr=1_100_000,
        online=True,
        counter_method=None,
        session_day=date(2026, 10, 15),
        label="فروش آنلاین",
    )
    assert await balance(container, await role(container, AccountRole.VAT_PAYABLE)) == -100_000
    assert await balance(container, await role(container, AccountRole.GATEWAY_FEES)) == 11_000
    assert await balance(container, await role(container, AccountRole.BANK)) == 1_089_000
    assert await balance(container, await role(container, AccountRole.GATEWAY)) == 0
    assert not await container.sales_posting().post_sale(
        reservation_id="r-1",
        amount_irr=1_100_000,
        online=True,
        counter_method=None,
        session_day=date(2026, 10, 15),
        label="again",
    )  # idempotent: already booked
    assert (await container.journal().search(JournalQuery(source=EntrySource.ONLINE_SALE))).total == 1
    await container.sales_posting().refund_sale(reservation_id="r-1", label="استرداد")
    assert await balance(container, await role(container, AccountRole.REFUNDS_PAYABLE)) == -1_100_000
    assert await balance(container, await role(container, AccountRole.VAT_PAYABLE)) == 0


async def test_in_accrual_mode_a_ticket_is_an_advance_until_its_session_day(
    container: ApplicationContainer, clock: FixedClock
) -> None:
    await container.accounting_settings().update(AccountingSettings(revenue_recognition=RevenueRecognition.ON_SESSION))
    await container.sales_posting().post_sale(
        reservation_id="r-2",
        amount_irr=1_000_000,
        online=True,
        counter_method=None,
        session_day=date(2026, 10, 16),
        label="x",
    )
    deferred, revenue = (
        await role(container, AccountRole.DEFERRED_REVENUE),
        await role(container, AccountRole.SALES_REVENUE),
    )
    assert await balance(container, deferred) == -1_000_000 and await balance(container, revenue) == 0
    assert await container.sales_posting().recognize_due() == 0  # session is two days away
    clock.advance(days=3)
    assert await container.sales_posting().recognize_due() == 1
    assert await container.sales_posting().recognize_due() == 0  # earned once
    assert await balance(container, deferred, date(2026, 10, 20)) == 0
    assert await balance(container, revenue, date(2026, 10, 20)) == -1_000_000


async def test_turning_automatic_posting_off_books_nothing(container: ApplicationContainer) -> None:
    await container.accounting_settings().update(AccountingSettings(auto_posting_enabled=False))
    sale_id = await counter_sale(container, CounterPaymentMethod.CASH)
    await AccountingEvents(container).book_sale(sale_id)
    assert (await container.journal().search(JournalQuery())).total == 0


async def test_old_reservations_are_booked_by_the_sync(container: ApplicationContainer) -> None:
    await counter_sale(container, CounterPaymentMethod.CASH, 200_000)
    await counter_sale(container, CounterPaymentMethod.TRANSFER, 300_000)
    first = await AccountingEvents(container).backfill(date(2026, 10, 1), date(2026, 10, 31))
    again = await AccountingEvents(container).backfill(date(2026, 10, 1), date(2026, 10, 31))
    assert (first, again) == (2, 0)  # a second run finds the entries and creates no new ones
    assert (await container.journal().search(JournalQuery(source=EntrySource.COUNTER_SALE))).total == 2


# ---------------------------------------------------------------- expenses, suppliers, assets, the till


async def test_an_expense_on_credit_becomes_a_supplier_debt_that_payments_clear_oldest_first(
    container: ApplicationContainer, clock: FixedClock
) -> None:
    fuel, cash = await code(container, "5101"), await role(container, AccountRole.CASH)
    vendor = await container.vendors().create(name="پمپ بنزین", phone="", note="")
    await container.bookkeeping().record_expense(
        day=date(2026, 8, 1),
        expense_account_id=fuel,
        amount_irr=1_000_000,
        vat_irr=100_000,
        paid_from_account_id=None,
        vendor_id=vendor.id,
        description="سوخت",
        created_by="owner",
    )
    await container.bookkeeping().record_expense(
        day=date(2026, 10, 10),
        expense_account_id=fuel,
        amount_irr=400_000,
        vat_irr=0,
        paid_from_account_id=None,
        vendor_id=vendor.id,
        description="سوخت",
        created_by="owner",
    )
    await container.bookkeeping().pay_vendor(
        day=TODAY, vendor_id=vendor.id, from_account_id=cash, amount_irr=1_000_000, description="", created_by="owner"
    )
    [row] = await container.vendors().list_with_balances(TODAY)
    assert row.balance is not None and row.balance.owed_irr == 400_000
    assert row.balance.age_0_30 == 400_000 and row.balance.age_over_90 == 0  # the August bill was paid first
    assert await balance(container, await role(container, AccountRole.VAT_RECEIVABLE)) == 100_000
    vat = await container.accounting_reports().vat_report(date(2026, 3, 21), TODAY)
    assert vat.paid_irr == 100_000 and vat.net_payable_irr == -100_000


async def test_an_expense_without_a_supplier_or_payment_source_is_refused(container: ApplicationContainer) -> None:
    with pytest.raises(Exception, match="تامین"):
        await container.bookkeeping().record_expense(
            day=TODAY,
            expense_account_id=await code(container, "5101"),
            amount_irr=1000,
            vat_irr=0,
            paid_from_account_id=None,
            vendor_id=None,
            description="",
            created_by="o",
        )


async def test_assets_are_depreciated_monthly_and_each_month_only_once(container: ApplicationContainer) -> None:
    karts = await role(container, AccountRole.FIXED_ASSET_KARTS)
    capital = await role(container, AccountRole.CAPITAL)
    await container.fixed_assets().register(
        name="کارت ۱",
        asset_account_id=karts,
        cost_irr=12_000_000,
        salvage_irr=0,
        in_service_date=date(2026, 9, 25),
        life_months=12,
        note="",
        paid_from_account_id=await role(container, AccountRole.BANK),
        vendor_id=None,
        post_purchase=True,
        created_by="owner",
    )
    assert await container.fixed_assets().run_depreciation(1405, 7, created_by="owner") == 1_000_000
    assert await container.fixed_assets().run_depreciation(1405, 7, created_by="owner") == 0
    assert await container.fixed_assets().run_depreciation(1405, 8, created_by="owner") == 1_000_000
    assert (
        await balance(container, await role(container, AccountRole.ACCUMULATED_DEPRECIATION), date(2026, 12, 1))
        == -2_000_000
    )
    [asset] = await container.fixed_assets().list_all()
    assert asset.book_value_irr == 10_000_000
    _ = capital


async def test_the_till_count_books_an_overage_or_shortage_and_cannot_be_closed_twice(
    container: ApplicationContainer,
) -> None:
    await container.accounting_settings().update(AccountingSettings())
    await AccountingEvents(container).book_sale(await counter_sale(container, CounterPaymentMethod.CASH, 400_000))
    assert await container.cash_closing().expected_cash(TODAY) == 4_000_000
    closing = await container.cash_closing().close_day(TODAY, counted_irr=3_900_000, note="", closed_by="owner")
    assert closing.difference_irr == -100_000
    assert await balance(container, await role(container, AccountRole.CASH_DIFFERENCE)) == 100_000
    assert await balance(container, await role(container, AccountRole.CASH)) == 3_900_000
    with pytest.raises(Exception, match="قبلا"):
        await container.cash_closing().close_day(TODAY, counted_irr=1, note="", closed_by="owner")


# ---------------------------------------------------------------- statements and the year end


async def test_the_balance_sheet_always_balances_and_the_year_end_moves_profit_to_retained_earnings(
    container: ApplicationContainer, clock: FixedClock
) -> None:
    cash, capital = await role(container, AccountRole.CASH), await role(container, AccountRole.CAPITAL)
    await post(container, cash, capital, 20_000_000, day=date(2026, 4, 1))
    await AccountingEvents(container).book_sale(await counter_sale(container, CounterPaymentMethod.CASH, 1_000_000))
    await container.bookkeeping().record_expense(
        day=TODAY,
        expense_account_id=await code(container, "5101"),
        amount_irr=3_000_000,
        vat_irr=0,
        paid_from_account_id=cash,
        vendor_id=None,
        description="",
        created_by="owner",
    )
    sheet = await container.accounting_reports().balance_sheet(TODAY)
    assert sheet.difference_irr == 0 and sheet.current_earnings_irr == 10_000_000 - 3_000_000
    income, _ = await container.accounting_reports().income_statement(date(2026, 3, 21), TODAY)
    assert (income.total_revenue, income.total_expenses, income.net_profit) == (10_000_000, 3_000_000, 7_000_000)
    with pytest.raises(Exception, match="هنوز تمام نشده"):
        await container.fiscal_years().close_year(1405, closed_by="owner")
    clock.advance(days=200)  # after the year end
    closing = await container.fiscal_years().close_year(1405, closed_by="owner")
    assert closing.source is EntrySource.CLOSING
    assert await container.fiscal_years().is_closed(1405)
    with pytest.raises(Exception, match="قبلا"):
        await container.fiscal_years().close_year(1405, closed_by="owner")
    after = await container.accounting_reports().balance_sheet(date(2027, 4, 1))
    assert after.difference_irr == 0 and after.current_earnings_irr == 0
    assert any(line.amount_irr == 7_000_000 for line in after.equity)  # retained earnings
    still, _ = await container.accounting_reports().income_statement(date(2026, 3, 21), date(2027, 3, 20))
    assert still.net_profit == 7_000_000  # the closed year's own statement is intact
    with pytest.raises(PeriodLockedError):
        await post(container, cash, capital, 1, day=date(2027, 1, 1))


async def test_sales_summary_splits_receipts_by_channel(container: ApplicationContainer) -> None:
    events = AccountingEvents(container)
    await events.book_sale(await counter_sale(container, CounterPaymentMethod.CASH, 100_000))
    await events.book_sale(await counter_sale(container, CounterPaymentMethod.CARD, 200_000))
    await events.book_sale(await counter_sale(container, CounterPaymentMethod.TRANSFER, 300_000))
    summary = await container.accounting_reports().sales_summary(TODAY, TODAY)
    # card and card-to-card both land in the bank, so they are one channel
    assert (summary.online_irr, summary.cash_irr, summary.card_irr, summary.revenue_irr) == (
        0,
        1_000_000,
        5_000_000,
        6_000_000,
    )
    online = await container.sales_posting().post_sale(
        reservation_id="r-online",
        amount_irr=700_000,
        online=True,
        counter_method=None,
        session_day=TODAY,
        label="آنلاین",
    )
    assert online and (await container.accounting_reports().sales_summary(TODAY, TODAY)).online_irr == 700_000


# ---------------------------------------------------------------- the owner-only API


@pytest.fixture
async def admin_api(container: ApplicationContainer) -> AsyncIterator[httpx.AsyncClient]:
    await container.manage_admins().ensure_bootstrap_owner(username="owner", password=OWNER_PASSWORD)
    transport = httpx.ASGITransport(
        app=create_app(container.settings, container), client=("203.0.113.9", 1), raise_app_exceptions=False
    )
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def login(client: httpx.AsyncClient, username: str = "owner", password: str = OWNER_PASSWORD) -> dict[str, str]:
    response = await client.post("/api/v1/admin/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"], "Origin": ORIGIN}


async def test_only_the_owner_sees_the_books(admin_api: httpx.AsyncClient) -> None:
    assert (await admin_api.get("/api/v1/admin/accounting/accounts")).status_code == 401
    owner = await login(admin_api)
    created = await admin_api.post(
        "/api/v1/admin/users",
        json={"username": "reza", "display_name": "رضا", "password": STAFF_PASSWORD, "role": "staff"},
        headers=owner,
    )
    assert created.status_code == 201
    admin_api.cookies.clear()
    staff = await login(admin_api, "reza", STAFF_PASSWORD)
    for path in ("/accounts", "/settings", "/journal", "/reports/dashboard"):
        assert (await admin_api.get(f"/api/v1/admin/accounting{path}", headers=staff)).status_code == 403, path


async def test_the_owner_posts_reverses_and_reads_reports_through_the_api(admin_api: httpx.AsyncClient) -> None:
    headers = await login(admin_api)
    accounts = (await admin_api.get("/api/v1/admin/accounting/accounts")).json()
    by_role = {a["role"]: a["id"] for a in accounts if a["role"]}
    body = {
        "date": "2026-10-14",
        "description": "سرمایه اولیه",
        "lines": [
            {"account_id": by_role["cash"], "debit_toman": 5_000_000},
            {"account_id": by_role["capital"], "credit_toman": 5_000_000},
        ],
    }
    posted = await admin_api.post("/api/v1/admin/accounting/journal", json=body, headers=headers)
    assert posted.status_code == 201, posted.text
    entry = posted.json()
    assert entry["number"] == 1 and entry["total_irr"] == 50_000_000 and entry["lines"][0]["account_name"] == "صندوق"
    unbalanced = {
        **body,
        "lines": [
            {"account_id": by_role["cash"], "debit_toman": 5},
            {"account_id": by_role["capital"], "credit_toman": 4},
        ],
    }
    assert (
        await admin_api.post("/api/v1/admin/accounting/journal", json=unbalanced, headers=headers)
    ).status_code == 422
    trial = (
        await admin_api.get(
            "/api/v1/admin/accounting/reports/trial-balance", params={"from": "2026-03-21", "to": "2026-10-14"}
        )
    ).json()
    assert trial["total_debit_irr"] == trial["total_credit_irr"] == 50_000_000
    sheet = (
        await admin_api.get("/api/v1/admin/accounting/reports/balance-sheet", params={"as_of": "2026-10-14"})
    ).json()
    assert sheet["difference_irr"] == 0 and sheet["total_assets_irr"] == 50_000_000
    reversed_ = await admin_api.post(
        f"/api/v1/admin/accounting/journal/{entry['id']}/reverse", json={"reason": "تست"}, headers=headers
    )
    assert reversed_.status_code == 201
    again = await admin_api.post(
        f"/api/v1/admin/accounting/journal/{entry['id']}/reverse", json={"reason": "تست"}, headers=headers
    )
    assert again.status_code == 409 and again.json()["code"] == "entry_already_reversed"
    dashboard = (await admin_api.get("/api/v1/admin/accounting/reports/dashboard")).json()
    assert dashboard["cash_irr"] == 0 and len(dashboard["trend"]) == 6


async def test_the_day_book_lists_only_the_kinds_of_entry_asked_for(
    admin_api: httpx.AsyncClient, container: ApplicationContainer
) -> None:
    headers = await login(admin_api)
    cash, bank = await role(container, AccountRole.CASH), await role(container, AccountRole.BANK)
    fuel = await code(container, "5101")
    await post(container, bank, await role(container, AccountRole.CAPITAL), 10_000_000)
    await AccountingEvents(container).book_sale(await counter_sale(container, CounterPaymentMethod.CASH, 790_000))
    spent = await admin_api.post(
        "/api/v1/admin/accounting/expenses",
        json={
            "date": "2026-10-14",
            "amount_toman": 120_000,
            "expense_account_id": str(fuel),
            "paid_from_account_id": str(cash),
        },
        headers=headers,
    )
    assert spent.status_code == 201, spent.text
    moved = await admin_api.post(
        "/api/v1/admin/accounting/transfers",
        json={"date": "2026-10-14", "amount_toman": 50_000, "from_account_id": str(cash), "to_account_id": str(bank)},
        headers=headers,
    )
    assert moved.status_code == 201, moved.text
    page = (await admin_api.get("/api/v1/admin/accounting/journal", params={"source": "expense,transfer"})).json()
    assert page["total"] == 2 and {e["source"] for e in page["items"]} == {"expense", "transfer"}
    assert (await admin_api.get("/api/v1/admin/accounting/journal", params={"source": "nonsense"})).status_code == 422
