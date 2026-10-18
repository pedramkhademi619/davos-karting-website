/** Shapes of the accounting API (backend/src/davos/api/schemas/accounting_presenter.py). All amounts are Rial (`*_irr`). */

import { fa } from "@/lib/format";
import { isoToJalaliParts, jalaliMonthLength, jalaliToIso, JALALI_MONTHS } from "@/lib/jalali";

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

export type SalesDay = { date: string; online_irr: number; cash_irr: number; card_irr: number; received_irr: number; revenue_irr: number };

export type SalesReport = { days: SalesDay[]; online_irr: number; cash_irr: number; card_irr: number; received_irr: number; revenue_irr: number };

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
  refunds_payable_irr: number;
  today_revenue_irr: number;
  month_revenue_irr: number;
  month_expenses_irr: number;
  month_profit_irr: number;
  trend: { key: string; revenue_irr: number; expenses_irr: number; profit_irr: number }[];
  top_expenses: StatementLine[];
};

/** Where money is kept. Card-reader and gateway balances are bank money on its way (older books), so they count as bank. */
export type Wallet = "cash" | "bank";
export const WALLET_LABEL: Record<Wallet, string> = { cash: "صندوق", bank: "بانک" };
const WALLET_OF_ROLE: Record<string, Wallet> = { cash: "cash", bank: "bank", pos: "bank", gateway: "bank" };

/** The entries the day book lists one by one; ticket sales are shown as one line per day instead. */
export const DAY_BOOK_SOURCES = ["expense", "income", "transfer", "payroll", "vendor_payment", "manual", "opening", "cash_close", "asset_purchase", "refund"];

/** The categories the owner picks from: active, postable, not a system account, of one type, in code order. */
export function categories(accounts: Account[], type: "expense" | "revenue", includeHidden = false): Account[] {
  return accounts
    .filter((a) => a.type === type && !a.is_group && !a.is_system && (includeHidden || a.active))
    .sort((a, b) => a.code.localeCompare(b.code, "en"));
}

/** The account of a wallet (the till or the main bank account). */
export function walletAccount(accounts: Account[], wallet: Wallet): Account | undefined {
  return accounts.find((a) => a.role === wallet);
}

export type EntryView = {
  /** in: money came in; out: money went out; move: between the till and the bank; other: no money moved (e.g. a refund owed). */
  direction: "in" | "out" | "move" | "other";
  amount_irr: number;
  title: string;
  category: string | null;
  wallet: string | null;
};

/** One journal entry in plain words: which way the money went, how much, for what, and from or into the till or bank. */
export function viewEntry(entry: Entry, byId: Map<string, Account>): EntryView {
  let moneyNet = 0;
  const wallets = new Set<Wallet>();
  let category: string | null = null;
  for (const line of entry.lines) {
    const account = byId.get(line.account_id);
    const wallet = account?.role ? WALLET_OF_ROLE[account.role] : undefined;
    if (wallet) {
      moneyNet += line.debit_irr - line.credit_irr;
      wallets.add(wallet);
    } else if (account && (account.type === "expense" || account.type === "revenue") && !category) {
      category = account.name;
    }
  }
  const walletText = [...wallets].map((w) => WALLET_LABEL[w]).join("، ");
  const title = entry.description || category || SOURCE_LABEL[entry.source] || "سند";
  if (entry.source === "transfer" && wallets.size === 2) {
    const paidFrom = entry.lines.find((l) => l.credit_irr > 0 && WALLET_OF_ROLE[byId.get(l.account_id)?.role ?? ""]);
    const from = WALLET_OF_ROLE[byId.get(paidFrom?.account_id ?? "")?.role ?? ""] ?? "cash";
    const to: Wallet = from === "cash" ? "bank" : "cash";
    return { direction: "move", amount_irr: entry.total_irr, title, category: null, wallet: `${WALLET_LABEL[from]} ← ${WALLET_LABEL[to]}` };
  }
  if (moneyNet > 0) return { direction: "in", amount_irr: moneyNet, title, category, wallet: walletText || null };
  if (moneyNet < 0) return { direction: "out", amount_irr: -moneyNet, title, category, wallet: walletText || null };
  return { direction: "other", amount_irr: entry.total_irr, title, category, wallet: null };
}

export const SOURCE_LABEL: Record<string, string> = {
  manual: "سند دستی",
  opening: "موجودی اول دوره",
  online_sale: "فروش آنلاین",
  counter_sale: "فروش حضوری",
  recognition: "شناسایی درآمد",
  refund: "استرداد بلیت",
  expense: "هزینه",
  income: "درآمد",
  vendor_payment: "پرداخت بدهی",
  transfer: "جابجایی پول",
  asset_purchase: "خرید تجهیزات",
  depreciation: "استهلاک",
  cash_close: "شمارش صندوق",
  payroll: "حقوق",
  reversal: "حذف سند",
  closing: "بستن سال",
};

/** Rial -> Toman text with Persian digits; a Rial that is not a whole Toman keeps one decimal so no digit is hidden. */
export function toman(irr: number): string {
  const value = irr / 10;
  const whole = Number.isInteger(value);
  const text = Math.abs(value).toLocaleString("en-US", { minimumFractionDigits: whole ? 0 : 1, maximumFractionDigits: whole ? 0 : 1 });
  return `${value < 0 ? "−" : ""}${fa(text).replace(/,/g, "٬")}`;
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

/** A Jalali month as `{ year, month }` (month 1..12), counted as an index so months can be stepped through. */
export type JalaliMonth = { year: number; month: number };

export function monthOf(iso: string): JalaliMonth {
  const { jy, jm } = isoToJalaliParts(iso);
  return { year: jy, month: jm };
}

export function shiftMonth({ year, month }: JalaliMonth, by: number): JalaliMonth {
  const index = year * 12 + (month - 1) + by;
  return { year: Math.floor(index / 12), month: (index % 12) + 1 };
}

export function monthBounds({ year, month }: JalaliMonth): [string, string] {
  return [jalaliToIso(year, month, 1), jalaliToIso(year, month, jalaliMonthLength(year, month))];
}

export function monthName({ year, month }: JalaliMonth): string {
  return `${JALALI_MONTHS[month - 1]} ${fa(year)}`;
}
