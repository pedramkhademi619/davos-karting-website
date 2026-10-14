from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from davos.modules.accounting.application.ports.account_ledger import AccountLedger
from davos.modules.accounting.application.use_cases.asset_with_book import AssetWithBook
from davos.modules.accounting.application.use_cases.vendor_with_balance import VendorWithBalance
from davos.modules.accounting.domain.entities.account import Account
from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.modules.accounting.domain.value_objects.accounting_dashboard import AccountingDashboard
from davos.modules.accounting.domain.value_objects.accounting_settings import AccountingSettings
from davos.modules.accounting.domain.value_objects.balance_sheet import BalanceSheet
from davos.modules.accounting.domain.value_objects.budget_row import BudgetRow
from davos.modules.accounting.domain.value_objects.cash_closing import CashClosing
from davos.modules.accounting.domain.value_objects.income_statement import IncomeStatement
from davos.modules.accounting.domain.value_objects.sales_summary import SalesSummary
from davos.modules.accounting.domain.value_objects.statement_line import StatementLine
from davos.modules.accounting.domain.value_objects.trial_balance_row import TrialBalanceRow
from davos.modules.accounting.domain.value_objects.vat_report import VatReport


def _id(value: uuid.UUID | None) -> str | None:
    return str(value) if value else None


class AccountingPresenter:
    """Turns accounting results into JSON. Every amount is in Rial (``*_irr``): accounting must not lose a digit, and
    the panel converts to Toman for display."""

    @staticmethod
    def account(a: Account) -> dict[str, Any]:
        return {
            "id": str(a.id),
            "code": a.code,
            "name": a.name,
            "type": a.type.value,
            "parent_id": _id(a.parent_id),
            "is_group": a.is_group,
            "role": a.role.value if a.role else None,
            "active": a.active,
            "is_system": a.is_system,
        }

    @staticmethod
    def settings(s: AccountingSettings) -> dict[str, Any]:
        return {
            "auto_posting_enabled": s.auto_posting_enabled,
            "vat_percent": s.vat_percent,
            "gateway_fee_percent": s.gateway_fee_bp / 100,
            "revenue_recognition": s.revenue_recognition.value,
            "locked_through": s.locked_through.isoformat() if s.locked_through else None,
        }

    @staticmethod
    def entry(
        e: JournalEntry, accounts: dict[uuid.UUID, Account] | None = None, vendors: dict[uuid.UUID, str] | None = None
    ) -> dict[str, Any]:
        lookup = accounts or {}
        return {
            "id": str(e.id),
            "number": e.number,
            "fiscal_year": e.fiscal_year,
            "date": e.entry_date.isoformat(),
            "description": e.description,
            "source": e.source.value,
            "source_ref": e.source_ref,
            "status": e.status.value,
            "reversed_by_id": _id(e.reversed_by_id),
            "reversal_of_id": _id(e.reversal_of_id),
            "created_by": e.created_by,
            "created_at": e.created_at.isoformat(),
            "total_irr": e.total_irr,
            "lines": [
                {
                    "account_id": str(line.account_id),
                    "account_code": lookup[line.account_id].code if line.account_id in lookup else "",
                    "account_name": lookup[line.account_id].name if line.account_id in lookup else "",
                    "debit_irr": line.debit_irr,
                    "credit_irr": line.credit_irr,
                    "memo": line.memo,
                    "vendor_id": _id(line.party_id),
                    "vendor_name": (vendors or {}).get(line.party_id, "") if line.party_id else "",
                }
                for line in e.lines
            ],
        }

    @staticmethod
    def statement_line(line: StatementLine) -> dict[str, Any]:
        return {
            "account_id": _id(line.account_id),
            "code": line.code,
            "name": line.name,
            "group": line.group,
            "amount_irr": line.amount_irr,
        }

    @classmethod
    def income_statement(cls, current: IncomeStatement, previous: IncomeStatement) -> dict[str, Any]:
        def one(s: IncomeStatement) -> dict[str, Any]:
            return {
                "from": s.date_from.isoformat(),
                "to": s.date_to.isoformat(),
                "revenue": [cls.statement_line(x) for x in s.revenue],
                "expenses": [cls.statement_line(x) for x in s.expenses],
                "total_revenue_irr": s.total_revenue,
                "total_expenses_irr": s.total_expenses,
                "net_profit_irr": s.net_profit,
            }

        return {**one(current), "previous": one(previous)}

    @classmethod
    def balance_sheet(cls, b: BalanceSheet) -> dict[str, Any]:
        return {
            "as_of": b.as_of.isoformat(),
            "assets": [cls.statement_line(x) for x in b.assets],
            "liabilities": [cls.statement_line(x) for x in b.liabilities],
            "equity": [cls.statement_line(x) for x in b.equity],
            "current_earnings_irr": b.current_earnings_irr,
            "total_assets_irr": b.total_assets,
            "total_liabilities_irr": b.total_liabilities,
            "total_equity_irr": b.total_equity,
            "difference_irr": b.difference_irr,
        }

    @staticmethod
    def trial_balance(rows: Sequence[TrialBalanceRow]) -> dict[str, Any]:
        return {
            "rows": [
                {
                    "account_id": str(r.account_id),
                    "code": r.code,
                    "name": r.name,
                    "type": r.account_type,
                    "opening_debit_irr": r.opening_debit,
                    "opening_credit_irr": r.opening_credit,
                    "debit_irr": r.debit,
                    "credit_irr": r.credit,
                    "closing_debit_irr": r.closing_debit,
                    "closing_credit_irr": r.closing_credit,
                }
                for r in rows
            ],
            "total_debit_irr": sum(r.debit for r in rows),
            "total_credit_irr": sum(r.credit for r in rows),
            "total_closing_debit_irr": sum(r.closing_debit for r in rows),
            "total_closing_credit_irr": sum(r.closing_credit for r in rows),
        }

    @staticmethod
    def ledger(account: Account, ledger: AccountLedger) -> dict[str, Any]:
        running = ledger.opening_net
        lines = []
        for line in ledger.lines:
            running += line.debit_irr - line.credit_irr
            lines.append(
                {
                    "entry_id": str(line.entry_id),
                    "number": line.entry_number,
                    "fiscal_year": line.fiscal_year,
                    "date": line.entry_date.isoformat(),
                    "description": line.description,
                    "memo": line.memo,
                    "debit_irr": line.debit_irr,
                    "credit_irr": line.credit_irr,
                    "balance_irr": running,
                    "source": line.source,
                }
            )
        return {
            "account": AccountingPresenter.account(account),
            "opening_irr": ledger.opening_net,
            "lines": lines,
            "closing_irr": running,
        }

    @staticmethod
    def sales(summary: SalesSummary) -> dict[str, Any]:
        return {
            "days": [
                {
                    "date": d.day.isoformat(),
                    "online_irr": d.online_irr,
                    "cash_irr": d.cash_irr,
                    "card_irr": d.card_irr,
                    "transfer_irr": d.transfer_irr,
                    "received_irr": d.received_irr,
                    "revenue_irr": d.revenue_irr,
                }
                for d in summary.days
            ],
            "online_irr": summary.online_irr,
            "cash_irr": summary.cash_irr,
            "card_irr": summary.card_irr,
            "transfer_irr": summary.transfer_irr,
            "received_irr": summary.received_irr,
            "revenue_irr": summary.revenue_irr,
        }

    @staticmethod
    def vat(report: VatReport) -> dict[str, Any]:
        return {
            "collected_irr": report.collected_irr,
            "paid_irr": report.paid_irr,
            "opening_balance_irr": report.opening_balance_irr,
            "net_payable_irr": report.net_payable_irr,
        }

    @staticmethod
    def vendor(item: VendorWithBalance) -> dict[str, Any]:
        b = item.balance
        return {
            "id": str(item.vendor.id),
            "name": item.vendor.name,
            "phone": item.vendor.phone,
            "note": item.vendor.note,
            "active": item.vendor.active,
            "owed_irr": b.owed_irr if b else 0,
            "age_0_30_irr": b.age_0_30 if b else 0,
            "age_31_60_irr": b.age_31_60 if b else 0,
            "age_61_90_irr": b.age_61_90 if b else 0,
            "age_over_90_irr": b.age_over_90 if b else 0,
            "advance_irr": b.advance_irr if b else 0,
        }

    @staticmethod
    def asset(item: AssetWithBook) -> dict[str, Any]:
        a = item.asset
        return {
            "id": str(a.id),
            "name": a.name,
            "asset_account_id": str(a.asset_account_id),
            "cost_irr": a.cost_irr,
            "salvage_irr": a.salvage_irr,
            "in_service_date": a.in_service_date.isoformat(),
            "life_months": a.life_months,
            "status": a.status.value,
            "note": a.note,
            "accumulated_irr": item.accumulated_irr,
            "book_value_irr": item.book_value_irr,
        }

    @staticmethod
    def budget_rows(rows: Sequence[BudgetRow]) -> list[dict[str, Any]]:
        return [
            {
                "account_id": str(r.account_id),
                "code": r.code,
                "name": r.name,
                "type": r.account_type,
                "budget_irr": r.budget_irr,
                "actual_irr": r.actual_irr,
                "variance_irr": r.variance_irr,
            }
            for r in rows
        ]

    @staticmethod
    def cash_closing(c: CashClosing) -> dict[str, Any]:
        return {
            "id": str(c.closing_id),
            "date": c.day.isoformat(),
            "expected_irr": c.expected_irr,
            "counted_irr": c.counted_irr,
            "difference_irr": c.difference_irr,
            "entry_id": _id(c.entry_id),
            "note": c.note,
            "closed_by": c.closed_by,
            "created_at": c.created_at.isoformat(),
        }

    @classmethod
    def dashboard(cls, d: AccountingDashboard) -> dict[str, Any]:
        return {
            "cash_irr": d.cash_irr,
            "bank_irr": d.bank_irr,
            "pos_irr": d.pos_irr,
            "gateway_irr": d.gateway_irr,
            "liquid_irr": d.liquid_irr,
            "payables_irr": d.payables_irr,
            "refunds_payable_irr": d.refunds_payable_irr,
            "vat_balance_irr": d.vat_balance_irr,
            "today_revenue_irr": d.today_revenue_irr,
            "month_revenue_irr": d.month_revenue_irr,
            "month_expenses_irr": d.month_expenses_irr,
            "month_profit_irr": d.month_profit_irr,
            "unrecognized_advances_irr": d.unrecognized_advances_irr,
            "trend": [
                {"key": p.key, "revenue_irr": p.revenue_irr, "expenses_irr": p.expenses_irr, "profit_irr": p.profit_irr}
                for p in d.trend
            ],
            "top_expenses": [cls.statement_line(x) for x in d.top_expenses],
        }

    @staticmethod
    def month_key_range(year: int, month: int) -> dict[str, str]:
        return {
            "from": FiscalCalendar.month_start(year, month).isoformat(),
            "to": FiscalCalendar.month_end(year, month).isoformat(),
        }
