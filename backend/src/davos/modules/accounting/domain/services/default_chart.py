from __future__ import annotations

from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.services.account_template import AccountTemplate

T = AccountType
R = AccountRole

# The chart a new installation starts with: a handful of plain income and expense categories a karting track really
# uses, plus the accounts automatic postings need (the ones with a ``role``; the admin panel keeps them out of sight).
# Codes follow the usual Iranian 1-5 grouping; the owner can add, rename or hide categories.
DEFAULT_CHART: tuple[AccountTemplate, ...] = (
    AccountTemplate("1", "دارایی‌ها", T.ASSET, None, True, None),
    AccountTemplate("1101", "صندوق", T.ASSET, "1", False, R.CASH),
    AccountTemplate("1110", "بانک", T.ASSET, "1", False, R.BANK),
    AccountTemplate("1120", "کارت‌خوان (تسویه‌نشده)", T.ASSET, "1", False, R.POS),
    AccountTemplate("1130", "درگاه پرداخت (تسویه‌نشده)", T.ASSET, "1", False, R.GATEWAY),
    AccountTemplate("1140", "طلب از دیگران", T.ASSET, "1", False, R.RECEIVABLES),
    AccountTemplate("1160", "مالیات ارزش افزوده خرید", T.ASSET, "1", False, R.VAT_RECEIVABLE),
    AccountTemplate("1201", "خودروها و تجهیزات", T.ASSET, "1", False, R.FIXED_ASSET_KARTS),
    AccountTemplate("1290", "استهلاک انباشته", T.ASSET, "1", False, R.ACCUMULATED_DEPRECIATION),
    AccountTemplate("2", "بدهی‌ها", T.LIABILITY, None, True, None),
    AccountTemplate("2101", "بدهی به فروشندگان", T.LIABILITY, "2", False, R.PAYABLES),
    AccountTemplate("2102", "مالیات ارزش افزوده فروش", T.LIABILITY, "2", False, R.VAT_PAYABLE),
    AccountTemplate("2103", "پیش‌دریافت بلیت", T.LIABILITY, "2", False, R.DEFERRED_REVENUE),
    AccountTemplate("2104", "استرداد به مشتریان", T.LIABILITY, "2", False, R.REFUNDS_PAYABLE),
    AccountTemplate("2105", "حقوق پرداختنی", T.LIABILITY, "2", False, R.SALARY_PAYABLE),
    AccountTemplate("3", "سرمایه", T.EQUITY, None, True, None),
    AccountTemplate("3101", "سرمایه", T.EQUITY, "3", False, R.CAPITAL),
    AccountTemplate("3103", "سود (زیان) انباشته", T.EQUITY, "3", False, R.RETAINED_EARNINGS),
    AccountTemplate("3104", "خلاصه سود و زیان", T.EQUITY, "3", False, R.INCOME_SUMMARY),
    AccountTemplate("3105", "تراز افتتاحیه", T.EQUITY, "3", False, R.OPENING_BALANCE),
    AccountTemplate("4", "درآمدها", T.REVENUE, None, True, None),
    AccountTemplate("4101", "فروش بلیت", T.REVENUE, "4", False, R.SALES_REVENUE),
    AccountTemplate("4102", "بوفه", T.REVENUE, "4", False, None),
    AccountTemplate("4104", "رویداد و مسابقه", T.REVENUE, "4", False, None),
    AccountTemplate("4201", "برگشت از فروش", T.REVENUE, "4", False, R.SALES_RETURNS),
    AccountTemplate("4301", "سایر درآمدها", T.REVENUE, "4", False, None),
    AccountTemplate("5", "هزینه‌ها", T.EXPENSE, None, True, None),
    AccountTemplate("5101", "سوخت", T.EXPENSE, "5", False, None),
    AccountTemplate("5102", "تعمیر و قطعات", T.EXPENSE, "5", False, None),
    AccountTemplate("5104", "بیمه", T.EXPENSE, "5", False, None),
    AccountTemplate("5105", "کلاه، لباس و تجهیزات ایمنی", T.EXPENSE, "5", False, None),
    AccountTemplate("5201", "حقوق و بیمه پرسنل", T.EXPENSE, "5", False, None),
    AccountTemplate("5301", "اجاره", T.EXPENSE, "5", False, None),
    AccountTemplate("5302", "قبض‌ها (آب، برق، گاز، تلفن، اینترنت)", T.EXPENSE, "5", False, None),
    AccountTemplate("5305", "متفرقه", T.EXPENSE, "5", False, None),
    AccountTemplate("5401", "تبلیغات", T.EXPENSE, "5", False, None),
    AccountTemplate("5402", "کارمزد بانک", T.EXPENSE, "5", False, R.GATEWAY_FEES),
    AccountTemplate("5501", "استهلاک", T.EXPENSE, "5", False, R.DEPRECIATION_EXPENSE),
    AccountTemplate("5502", "مالیات و عوارض", T.EXPENSE, "5", False, None),
    AccountTemplate("5504", "کسری و اضافه صندوق", T.EXPENSE, "5", False, R.CASH_DIFFERENCE),
)
