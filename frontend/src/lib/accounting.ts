/** Shapes of the accounting API (backend/src/davos/api/schemas/accounting_presenter.py). All amounts are Rial (`*_irr`). */

import { fa } from "@/lib/format";

export type AccountType = "asset" | "liability" | "equity" | "revenue" | "expense";

export type Account = {
  id: string;
  code: string;
  name: string;
  type: AccountType;
  parent_id: string | null;
  is_group: boolean;
  role: string | null;
  active: boolean;
  is_system: boolean;
};

export type EntryLine = {
  account_id: string;
  account_code: string;
  account_name: string;
  debit_irr: number;
  credit_irr: number;
  memo: string;
  vendor_id: string | null;
  vendor_name: string;
};

export type Entry = {
  id: string;
  number: number;
  fiscal_year: number;
  date: string;
  description: string;
  source: string;
  source_ref: string | null;
  status: "posted" | "reversed";
  reversed_by_id: string | null;
  reversal_of_id: string | null;
  created_by: string;
  created_at: string;
  total_irr: number;
  lines: EntryLine[];
};

export type AccountingSettings = {
  auto_posting_enabled: boolean;
  vat_percent: number;
  gateway_fee_percent: number;
  revenue_recognition: "on_payment" | "on_session";
  locked_through: string | null;
};

export type Vendor = {
  id: string;
  name: string;
  phone: string;
  note: string;
  active: boolean;
  owed_irr: number;
  age_0_30_irr: number;
  age_31_60_irr: number;
  age_61_90_irr: number;
  age_over_90_irr: number;
  advance_irr: number;
};

export type Asset = {
  id: string;
  name: string;
  asset_account_id: string;
  cost_irr: number;
  salvage_irr: number;
  in_service_date: string;
  life_months: number;
  status: "active" | "disposed";
  note: string;
  accumulated_irr: number;
  book_value_irr: number;
};

export type StatementLine = { account_id: string | null; code: string; name: string; group: string; amount_irr: number };

export type IncomeStatementPeriod = {
  from: string;
  to: string;
  revenue: StatementLine[];
  expenses: StatementLine[];
  total_revenue_irr: number;
  total_expenses_irr: number;
  net_profit_irr: number;
};
export type IncomeStatement = IncomeStatementPeriod & { previous: IncomeStatementPeriod };

export type BalanceSheet = {
  as_of: string;
  assets: StatementLine[];
  liabilities: StatementLine[];
  equity: StatementLine[];
  current_earnings_irr: number;
  total_assets_irr: number;
  total_liabilities_irr: number;
  total_equity_irr: number;
  difference_irr: number;
};

export type TrialBalance = {
  rows: {
    account_id: string;
    code: string;
    name: string;
    type: AccountType;
    opening_debit_irr: number;
    opening_credit_irr: number;
    debit_irr: number;
    credit_irr: number;
    closing_debit_irr: number;
    closing_credit_irr: number;
  }[];
  total_debit_irr: number;
  total_credit_irr: number;
  total_closing_debit_irr: number;
  total_closing_credit_irr: number;
};

export type Ledger = {
  account: Account;
  opening_irr: number;
  closing_irr: number;
  lines: {
    entry_id: string;
    number: number;
    fiscal_year: number;
    date: string;
    description: string;
    memo: string;
    debit_irr: number;
    credit_irr: number;
    balance_irr: number;
    source: string;
  }[];
};

export type SalesReport = {
  days: { date: string; online_irr: number; cash_irr: number; card_irr: number; transfer_irr: number; received_irr: number; revenue_irr: number }[];
  online_irr: number;
  cash_irr: number;
  card_irr: number;
  transfer_irr: number;
  received_irr: number;
  revenue_irr: number;
};

export type VatReport = { collected_irr: number; paid_irr: number; opening_balance_irr: number; net_payable_irr: number };

export type BudgetRow = { account_id: string; code: string; name: string; type: AccountType; budget_irr: number; actual_irr: number; variance_irr: number };

export type CashClosing = {
  id: string;
  date: string;
  expected_irr: number;
  counted_irr: number;
  difference_irr: number;
  entry_id: string | null;
  note: string;
  closed_by: string;
  created_at: string;
};

export type AccountingDashboard = {
  cash_irr: number;
  bank_irr: number;
  pos_irr: number;
  gateway_irr: number;
  liquid_irr: number;
  payables_irr: number;
  refunds_payable_irr: number;
  vat_balance_irr: number;
  today_revenue_irr: number;
  month_revenue_irr: number;
  month_expenses_irr: number;
  month_profit_irr: number;
  unrecognized_advances_irr: number;
  trend: { key: string; revenue_irr: number; expenses_irr: number; profit_irr: number }[];
  top_expenses: StatementLine[];
};

export const ACCOUNT_TYPE_LABEL: Record<AccountType, string> = {
  asset: "دارایی",
  liability: "بدهی",
  equity: "حقوق صاحبان سرمایه",
  revenue: "درآمد",
  expense: "هزینه",
};

export const SOURCE_LABEL: Record<string, string> = {
  manual: "سند دستی",
  opening: "افتتاحیه",
  online_sale: "فروش آنلاین",
  counter_sale: "فروش حضوری",
  recognition: "شناسایی درآمد",
  refund: "استرداد",
  expense: "هزینه",
  income: "درآمد متفرقه",
  vendor_payment: "پرداخت به تامین‌کننده",
  transfer: "انتقال / پرداخت",
  asset_purchase: "خرید دارایی",
  depreciation: "استهلاک",
  cash_close: "صندوق‌گردانی",
  payroll: "حقوق",
  reversal: "ابطال",
  closing: "بستن سال",
};

/** Rial -> Toman text with Persian digits; a Rial that is not a whole Toman keeps one decimal so no digit is hidden. */
export function toman(irr: number): string {
  const value = irr / 10;
  const whole = Number.isInteger(value);
  const text = Math.abs(value).toLocaleString("en-US", { minimumFractionDigits: whole ? 0 : 1, maximumFractionDigits: whole ? 0 : 1 });
  return `${value < 0 ? "−" : ""}${fa(text).replace(/,/g, "٬")}`;
}

/** Like `toman` but a zero is shown as a dash (for tables). */
export function tomanOrDash(irr: number): string {
  return irr === 0 ? "—" : toman(irr);
}

/** Saves rows as a UTF-8 CSV (with a byte-order mark so Excel reads Persian text correctly). */
export function downloadCsv(name: string, header: string[], rows: (string | number)[][]): void {
  const quote = (value: string | number) => `"${String(value).replace(/"/g, '""')}"`;
  const text = [header, ...rows].map((row) => row.map(quote).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob(["﻿" + text], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `${name}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Rial amount -> plain Toman number for a CSV cell (no grouping, so spreadsheets can add it up). */
export function csvToman(irr: number): number {
  return irr / 10;
}
