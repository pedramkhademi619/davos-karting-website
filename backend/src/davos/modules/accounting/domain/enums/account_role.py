from enum import StrEnum


class AccountRole(StrEnum):
    """The job a system account does. Automatic postings find accounts by role, never by code, so the owner can renumber
    or rename the chart freely."""

    CASH = "cash"  # the till
    BANK = "bank"  # the main bank account
    POS = "pos"  # card-reader money not yet in the bank
    GATEWAY = "gateway"  # online payments the gateway has not yet paid out
    RECEIVABLES = "receivables"
    VAT_RECEIVABLE = "vat_receivable"  # VAT paid on purchases
    FIXED_ASSET_KARTS = "fixed_asset_karts"
    ACCUMULATED_DEPRECIATION = "accumulated_depreciation"
    PAYABLES = "payables"  # owed to suppliers
    VAT_PAYABLE = "vat_payable"  # VAT collected on sales
    DEFERRED_REVENUE = "deferred_revenue"  # tickets paid for sessions not yet driven
    REFUNDS_PAYABLE = "refunds_payable"  # money owed back to customers
    SALARY_PAYABLE = "salary_payable"
    CAPITAL = "capital"
    RETAINED_EARNINGS = "retained_earnings"
    INCOME_SUMMARY = "income_summary"
    OPENING_BALANCE = "opening_balance"
    SALES_REVENUE = "sales_revenue"
    SALES_RETURNS = "sales_returns"
    GATEWAY_FEES = "gateway_fees"
    DEPRECIATION_EXPENSE = "depreciation_expense"
    CASH_DIFFERENCE = "cash_difference"  # till overage / shortage
