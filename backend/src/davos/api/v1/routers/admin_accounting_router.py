from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from davos.api.dependencies.admin_authentication import require_permission
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.accounting_account_request import AccountingAccountRequest
from davos.api.schemas.accounting_asset_request import AccountingAssetRequest
from davos.api.schemas.accounting_backfill_request import AccountingBackfillRequest
from davos.api.schemas.accounting_budget_request import AccountingBudgetRequest
from davos.api.schemas.accounting_cash_closing_request import AccountingCashClosingRequest
from davos.api.schemas.accounting_depreciation_request import AccountingDepreciationRequest
from davos.api.schemas.accounting_expense_request import AccountingExpenseRequest
from davos.api.schemas.accounting_income_request import AccountingIncomeRequest
from davos.api.schemas.accounting_journal_entry_request import AccountingJournalEntryRequest
from davos.api.schemas.accounting_payment_request import AccountingPaymentRequest
from davos.api.schemas.accounting_presenter import AccountingPresenter
from davos.api.schemas.accounting_reverse_request import AccountingReverseRequest
from davos.api.schemas.accounting_settings_request import AccountingSettingsRequest
from davos.api.schemas.accounting_transfer_request import AccountingTransferRequest
from davos.api.schemas.accounting_vendor_request import AccountingVendorRequest
from davos.composition.accounting_events import AccountingEvents
from davos.composition.application_container import ApplicationContainer
from davos.modules.accounting.application.ports.journal_query import JournalQuery
from davos.modules.accounting.domain.entities.account import Account
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.enums.revenue_recognition import RevenueRecognition
from davos.modules.accounting.domain.errors.account_not_found_error import AccountNotFoundError
from davos.modules.accounting.domain.errors.asset_not_found_error import AssetNotFoundError
from davos.modules.accounting.domain.errors.entry_not_found_error import EntryNotFoundError
from davos.modules.accounting.domain.errors.vendor_not_found_error import VendorNotFoundError
from davos.modules.accounting.domain.services.tehran_calendar import TehranCalendar
from davos.modules.accounting.domain.value_objects.accounting_settings import AccountingSettings
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.modules.administration.domain.enums.admin_permission import AdminPermission
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError

router = APIRouter(prefix="/admin/accounting", tags=["accounting"])

_ALLOWED = require_permission(AdminPermission.ACCOUNTING)

_P = AccountingPresenter
DateFrom = Annotated[date, Query(alias="from")]
DateTo = Annotated[date, Query(alias="to")]
Json = dict[str, Any]


def _uuid(raw: str | None, error: type[NotFoundError] = NotFoundError) -> uuid.UUID:
    try:
        return uuid.UUID(str(raw))
    except ValueError as exc:
        raise error from exc


def _optional(raw: str | None, error: type[NotFoundError]) -> uuid.UUID | None:
    return _uuid(raw, error) if raw else None


def _irr(toman: int) -> int:
    return toman * 10


async def _lookups(container: ApplicationContainer) -> tuple[dict[uuid.UUID, Account], dict[uuid.UUID, str]]:
    accounts = {a.id: a for a in await container.chart_of_accounts().list_all()}
    vendors = {
        v.vendor.id: v.vendor.name
        for v in await container.vendors().list_with_balances(TehranCalendar.today(container.clock.now()))
    }
    return accounts, vendors


# ---- chart of accounts and settings -----------------------------------------------------------------------------


@router.get("/accounts", summary="The chart of accounts (owner only)")
async def accounts(
    _: AuthenticatedAdminRequest = Depends(_ALLOWED), container: ApplicationContainer = Depends(get_container)
) -> list[Json]:
    return [_P.account(a) for a in await container.chart_of_accounts().list_all()]


@router.post("/accounts", status_code=201, summary="Add an account")
async def create_account(
    body: AccountingAccountRequest,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    account = await container.chart_of_accounts().create(
        code=body.code,
        name=body.name,
        account_type=AccountType(body.type),
        parent_id=_optional(body.parent_id, AccountNotFoundError),
        is_group=body.is_group,
    )
    return _P.account(account)


@router.put("/accounts/{account_id}", summary="Rename, renumber, or deactivate an account")
async def update_account(
    account_id: str,
    body: AccountingAccountRequest,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    account = await container.chart_of_accounts().update(
        _uuid(account_id, AccountNotFoundError), code=body.code, name=body.name, active=body.active
    )
    return _P.account(account)


@router.delete("/accounts/{account_id}", status_code=204, summary="Delete (deactivate) an unused account")
async def delete_account(
    account_id: str,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.chart_of_accounts().delete(_uuid(account_id, AccountNotFoundError))
    return Response(status_code=204)


@router.get("/settings", summary="Accounting settings")
async def get_settings(
    _: AuthenticatedAdminRequest = Depends(_ALLOWED), container: ApplicationContainer = Depends(get_container)
) -> Json:
    return _P.settings(await container.accounting_settings().get())


@router.put("/settings", summary="Change the accounting settings")
async def update_settings(
    body: AccountingSettingsRequest,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    saved = await container.accounting_settings().update(
        AccountingSettings(
            auto_posting_enabled=body.auto_posting_enabled,
            vat_percent=body.vat_percent,
            gateway_fee_bp=round(body.gateway_fee_percent * 100),
            revenue_recognition=RevenueRecognition(body.revenue_recognition),
            locked_through=body.locked_through,
        )
    )
    return _P.settings(saved)


# ---- journal ----------------------------------------------------------------------------------------------------


@router.get("/journal", summary="Journal entries (دفتر روزنامه)")
async def journal(
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    account_id: str | None = None,
    q: Annotated[str, Query(max_length=80)] = "",
    source: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    page = await container.journal().search(
        JournalQuery(
            date_from=date_from,
            date_to=date_to,
            account_id=_optional(account_id, AccountNotFoundError),
            text=q,
            source=EntrySource(source) if source else None,
            offset=offset,
            limit=limit,
        )
    )
    accounts_by_id, vendors = await _lookups(container)
    return {"items": [_P.entry(e, accounts_by_id, vendors) for e in page.items], "total": page.total}


@router.get("/journal/{entry_id}", summary="One entry with its lines")
async def journal_entry(
    entry_id: str,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    entry = await container.journal().get(_uuid(entry_id, EntryNotFoundError))
    accounts_by_id, vendors = await _lookups(container)
    return _P.entry(entry, accounts_by_id, vendors)


@router.post("/journal", status_code=201, summary="Post a manual entry")
async def post_entry(
    body: AccountingJournalEntryRequest,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    lines = [
        JournalLine(
            account_id=_uuid(line.account_id, AccountNotFoundError),
            debit_irr=_irr(line.debit_toman),
            credit_irr=_irr(line.credit_toman),
            memo=line.memo,
            party_id=_optional(line.vendor_id, VendorNotFoundError),
        )
        for line in body.lines
    ]
    entry = await container.journal().post_manual(
        entry_date=body.date,
        description=body.description,
        lines=lines,
        created_by=auth.admin.username,
        opening=body.opening,
    )
    accounts_by_id, vendors = await _lookups(container)
    return _P.entry(entry, accounts_by_id, vendors)


@router.post("/journal/{entry_id}/reverse", status_code=201, summary="Cancel an entry with a reversing entry")
async def reverse_entry(
    entry_id: str,
    body: AccountingReverseRequest,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    reversal = await container.journal().reverse(
        _uuid(entry_id, EntryNotFoundError), reason=body.reason, created_by=auth.admin.username
    )
    accounts_by_id, vendors = await _lookups(container)
    return _P.entry(reversal, accounts_by_id, vendors)


# ---- everyday entries -------------------------------------------------------------------------------------------


@router.post("/expenses", status_code=201, summary="Record an expense (paid now or on credit)")
async def expense(
    body: AccountingExpenseRequest,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    entry = await container.bookkeeping().record_expense(
        day=body.date,
        expense_account_id=_uuid(body.expense_account_id, AccountNotFoundError),
        amount_irr=_irr(body.amount_toman),
        vat_irr=_irr(body.vat_toman),
        paid_from_account_id=_optional(body.paid_from_account_id, AccountNotFoundError),
        vendor_id=_optional(body.vendor_id, VendorNotFoundError),
        description=body.description,
        created_by=auth.admin.username,
    )
    return _P.entry(entry, *(await _lookups(container)))


@router.post("/income", status_code=201, summary="Record money received that is not a ticket")
async def income(
    body: AccountingIncomeRequest,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    entry = await container.bookkeeping().record_income(
        day=body.date,
        revenue_account_id=_uuid(body.revenue_account_id, AccountNotFoundError),
        amount_irr=_irr(body.amount_toman),
        vat_irr=_irr(body.vat_toman),
        deposit_account_id=_uuid(body.deposit_account_id, AccountNotFoundError),
        description=body.description,
        created_by=auth.admin.username,
    )
    return _P.entry(entry, *(await _lookups(container)))


@router.post("/transfers", status_code=201, summary="Move money between cash and bank accounts")
async def transfer(
    body: AccountingTransferRequest,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    entry = await container.bookkeeping().transfer(
        day=body.date,
        from_account_id=_uuid(body.from_account_id, AccountNotFoundError),
        to_account_id=_uuid(body.to_account_id, AccountNotFoundError),
        amount_irr=_irr(body.amount_toman),
        description=body.description,
        created_by=auth.admin.username,
    )
    return _P.entry(entry, *(await _lookups(container)))


@router.post("/payments", status_code=201, summary="Pay a supplier, or hand a refund back to a customer")
async def payment(
    body: AccountingPaymentRequest,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    source = _uuid(body.from_account_id, AccountNotFoundError)
    if body.vendor_id:
        entry = await container.bookkeeping().pay_vendor(
            day=body.date,
            vendor_id=_uuid(body.vendor_id, VendorNotFoundError),
            from_account_id=source,
            amount_irr=_irr(body.amount_toman),
            description=body.description,
            created_by=auth.admin.username,
        )
    else:
        entry = await container.bookkeeping().pay_customer_refund(
            day=body.date,
            from_account_id=source,
            amount_irr=_irr(body.amount_toman),
            description=body.description,
            created_by=auth.admin.username,
        )
    return _P.entry(entry, *(await _lookups(container)))


# ---- vendors, assets, budget, cash, year-end --------------------------------------------------------------------


@router.get("/vendors", summary="Suppliers with what is owed to each")
async def vendors(
    as_of: Annotated[date | None, Query()] = None,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> list[Json]:
    return [
        _P.vendor(v)
        for v in await container.vendors().list_with_balances(as_of or TehranCalendar.today(container.clock.now()))
    ]


@router.post("/vendors", status_code=201, summary="Add a supplier")
async def create_vendor(
    body: AccountingVendorRequest,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    vendor = await container.vendors().create(name=body.name, phone=body.phone, note=body.note)
    return {"id": str(vendor.id), "name": vendor.name}


@router.put("/vendors/{vendor_id}", summary="Edit a supplier")
async def update_vendor(
    vendor_id: str,
    body: AccountingVendorRequest,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    vendor = await container.vendors().update(
        _uuid(vendor_id, VendorNotFoundError), name=body.name, phone=body.phone, note=body.note, active=body.active
    )
    return {"id": str(vendor.id), "name": vendor.name}


@router.get("/assets", summary="Fixed assets with depreciation")
async def assets(
    _: AuthenticatedAdminRequest = Depends(_ALLOWED), container: ApplicationContainer = Depends(get_container)
) -> list[Json]:
    return [_P.asset(a) for a in await container.fixed_assets().list_all()]


@router.post("/assets", status_code=201, summary="Register an asset (and book its purchase)")
async def create_asset(
    body: AccountingAssetRequest,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    asset = await container.fixed_assets().register(
        name=body.name,
        asset_account_id=_uuid(body.asset_account_id, AccountNotFoundError),
        cost_irr=_irr(body.cost_toman),
        salvage_irr=_irr(body.salvage_toman),
        in_service_date=body.in_service_date,
        life_months=body.life_months,
        note=body.note,
        paid_from_account_id=_optional(body.paid_from_account_id, AccountNotFoundError),
        vendor_id=_optional(body.vendor_id, VendorNotFoundError),
        post_purchase=body.post_purchase,
        created_by=auth.admin.username,
    )
    return {"id": str(asset.id), "name": asset.name}


@router.post("/assets/{asset_id}/dispose", status_code=204, summary="Mark an asset as sold or scrapped")
async def dispose_asset(
    asset_id: str,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.fixed_assets().dispose(_uuid(asset_id, AssetNotFoundError))
    return Response(status_code=204)


@router.post("/depreciation", summary="Book one month's depreciation")
async def depreciation(
    body: AccountingDepreciationRequest,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    total = await container.fixed_assets().run_depreciation(body.year, body.month, created_by=auth.admin.username)
    return {"total_irr": total}


@router.get("/budget", summary="Budget against actual")
async def budget_report(
    year: Annotated[int, Query(ge=1300, le=1600)],
    month_from: Annotated[int, Query(ge=1, le=12)] = 1,
    month_to: Annotated[int, Query(ge=1, le=12)] = 12,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> list[Json]:
    return _P.budget_rows(await container.budgets().report(year, month_from, month_to))


@router.put("/budget", status_code=204, summary="Set a monthly (or yearly, spread evenly) budget")
async def set_budget(
    body: AccountingBudgetRequest,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    account_id = _uuid(body.account_id, AccountNotFoundError)
    if body.month is None:
        await container.budgets().set_whole_year(account_id, body.year, _irr(body.amount_toman))
    else:
        await container.budgets().set_month(account_id, body.year, body.month, _irr(body.amount_toman))
    return Response(status_code=204)


@router.get("/cash", summary="Till counts and what the books say the till should hold")
async def cash(
    day: Annotated[date | None, Query(alias="date")] = None,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    target = day or TehranCalendar.today(container.clock.now())
    return {
        "date": target.isoformat(),
        "expected_irr": await container.cash_closing().expected_cash(target),
        "closings": [_P.cash_closing(c) for c in await container.cash_closing().recent()],
    }


@router.post("/cash", status_code=201, summary="Close the till for a day")
async def close_cash(
    body: AccountingCashClosingRequest,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    closing = await container.cash_closing().close_day(
        body.date, counted_irr=_irr(body.counted_toman), note=body.note, closed_by=auth.admin.username
    )
    return _P.cash_closing(closing)


@router.get("/fiscal-years/{year}", summary="Has this fiscal year been closed?")
async def fiscal_year(
    year: int,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    return {"year": year, "closed": await container.fiscal_years().is_closed(year)}


@router.post("/fiscal-years/{year}/close", status_code=201, summary="Close the fiscal year (locks it)")
async def close_year(
    year: int,
    auth: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    entry = await container.fiscal_years().close_year(year, closed_by=auth.admin.username)
    return _P.entry(entry, *(await _lookups(container)))


@router.post("/sync", summary="Book reservations that have no sale entry yet, and earn due advances")
async def sync(
    body: AccountingBackfillRequest,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    created = await AccountingEvents(container).backfill(body.date_from, body.date_to)
    recognized = await container.sales_posting().recognize_due()
    return {"sales_booked": created, "revenue_recognized": recognized}


# ---- reports ----------------------------------------------------------------------------------------------------


@router.get("/reports/dashboard", summary="Financial dashboard")
async def dashboard(
    _: AuthenticatedAdminRequest = Depends(_ALLOWED), container: ApplicationContainer = Depends(get_container)
) -> Json:
    return _P.dashboard(await container.accounting_reports().dashboard())


@router.get("/reports/trial-balance", summary="Trial balance (تراز آزمایشی)")
async def trial_balance(
    date_from: DateFrom,
    date_to: DateTo,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    return _P.trial_balance(await container.accounting_reports().trial_balance(date_from, date_to))


@router.get("/reports/ledger", summary="General ledger of one account (دفتر کل)")
async def ledger(
    account_id: str,
    date_from: DateFrom,
    date_to: DateTo,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    account, lines = await container.accounting_reports().general_ledger(
        _uuid(account_id, AccountNotFoundError), date_from, date_to
    )
    return _P.ledger(account, lines)


@router.get("/reports/income-statement", summary="Profit and loss (سود و زیان)")
async def income_statement(
    date_from: DateFrom,
    date_to: DateTo,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    current, previous = await container.accounting_reports().income_statement(date_from, date_to)
    return _P.income_statement(current, previous)


@router.get("/reports/balance-sheet", summary="Balance sheet (ترازنامه)")
async def balance_sheet(
    as_of: Annotated[date, Query()],
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    return _P.balance_sheet(await container.accounting_reports().balance_sheet(as_of))


@router.get("/reports/sales", summary="Ticket sales by day and channel")
async def sales(
    date_from: DateFrom,
    date_to: DateTo,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    return _P.sales(await container.accounting_reports().sales_summary(date_from, date_to))


@router.get("/reports/vat", summary="VAT collected and paid")
async def vat(
    date_from: DateFrom,
    date_to: DateTo,
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> Json:
    return _P.vat(await container.accounting_reports().vat_report(date_from, date_to))


@router.get("/reports/cash-position", summary="Balances of cash, bank, card reader and gateway")
async def cash_position(
    as_of: Annotated[date, Query()],
    _: AuthenticatedAdminRequest = Depends(_ALLOWED),
    container: ApplicationContainer = Depends(get_container),
) -> list[Json]:
    return [_P.statement_line(line) for line in await container.accounting_reports().cash_position(as_of)]
