"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Kpi, Table, cell } from "@/components/admin/admin-ui";
import { SingleDatePicker } from "@/components/admin/date-picker-field";
import { AccountSelect, Field } from "@/components/admin/accounting/accounting-fields";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import {
  SOURCE_LABEL,
  csvToman,
  downloadCsv,
  toman,
  tomanOrDash,
  type Account,
  type BalanceSheet,
  type IncomeStatement,
  type Ledger,
  type SalesReport,
  type StatementLine,
  type TrialBalance,
  type VatReport,
  type Vendor,
} from "@/lib/accounting";
import { fa } from "@/lib/format";
import { addDays, currentBusinessDay, isoToJalali, isoToJalaliParts, jalaliToIso, jalaliMonthLength } from "@/lib/jalali";

type ReportId = "income" | "balance" | "trial" | "ledger" | "sales" | "vat" | "cash" | "vendors";

const REPORTS: { id: ReportId; label: string; range: "period" | "date" | "none" }[] = [
  { id: "income", label: "سود و زیان", range: "period" },
  { id: "balance", label: "ترازنامه", range: "date" },
  { id: "trial", label: "تراز آزمایشی", range: "period" },
  { id: "ledger", label: "دفتر کل (یک حساب)", range: "period" },
  { id: "sales", label: "فروش بلیت", range: "period" },
  { id: "vat", label: "مالیات ارزش افزوده", range: "period" },
  { id: "cash", label: "موجودی نقد و بانک", range: "date" },
  { id: "vendors", label: "بدهی به تامین‌کنندگان", range: "none" },
];

function monthRange(offset: number): [string, string] {
  const { jy, jm } = isoToJalaliParts(currentBusinessDay());
  const index = jy * 12 + (jm - 1) + offset;
  const year = Math.floor(index / 12);
  const month = (index % 12) + 1;
  return [jalaliToIso(year, month, 1), jalaliToIso(year, month, jalaliMonthLength(year, month))];
}

function yearRange(): [string, string] {
  const { jy } = isoToJalaliParts(currentBusinessDay());
  return [jalaliToIso(jy, 1, 1), jalaliToIso(jy, 12, jalaliMonthLength(jy, 12))];
}

/** Every statement the books can produce, for any period, with a CSV export for the accountant. */
export function ReportsView({ accounts, vendors }: { accounts: Account[]; vendors: Vendor[] }) {
  const { call } = useAdmin();
  const [report, setReport] = useState<ReportId>("income");
  const [initial] = useState(() => monthRange(0));
  const [from, setFrom] = useState(initial[0]);
  const [to, setTo] = useState(initial[1]);
  const [account, setAccount] = useState("");
  const [data, setData] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const kind = REPORTS.find((r) => r.id === report)?.range ?? "period";

  const load = useCallback(async () => {
    if (report === "vendors" || (report === "ledger" && !account)) {
      setData(null);
      return;
    }
    setLoading(true);
    try {
      const path = {
        income: "/accounting/reports/income-statement",
        balance: "/accounting/reports/balance-sheet",
        trial: "/accounting/reports/trial-balance",
        ledger: "/accounting/reports/ledger",
        sales: "/accounting/reports/sales",
        vat: "/accounting/reports/vat",
        cash: "/accounting/reports/cash-position",
      }[report];
      const query = kind === "date" ? { as_of: to } : report === "ledger" ? { account_id: account, from, to } : { from, to };
      setData(await call<unknown>(path, { query }));
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [call, report, from, to, account, kind]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reloads when the report or period changes
    void load();
  }, [load]);

  const preset = (range: [string, string]) => {
    setFrom(range[0]);
    setTo(range[1]);
  };

  return (
    <div className="space-y-6">
      <div role="tablist" aria-label="گزارش‌ها" className="flex flex-wrap gap-2">
        {REPORTS.map((r) => (
          <button
            key={r.id}
            type="button"
            role="tab"
            aria-selected={report === r.id}
            onClick={() => setReport(r.id)}
            className={`rounded-full px-4 py-2 text-sm font-bold ring-1 transition-colors ${report === r.id ? "bg-ink text-white ring-ink" : "bg-surface text-fg-muted ring-line-strong hover:text-fg"}`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {kind !== "none" && (
        <div className="flex flex-wrap items-end gap-3">
          {kind === "period" && (
            <Field label="از تاریخ">
              <SingleDatePicker value={from} onChange={setFrom} label="از تاریخ" />
            </Field>
          )}
          <Field label={kind === "period" ? "تا تاریخ" : "تا پایان روز"}>
            <SingleDatePicker value={to} onChange={setTo} label="تا تاریخ" />
          </Field>
          {report === "ledger" && (
            <div className="w-72">
              <AccountSelect label="حساب" accounts={accounts.map((a) => ({ ...a, is_group: false }))} value={account} onChange={setAccount} />
            </div>
          )}
          {kind === "period" && (
            <div className="flex flex-wrap gap-2 pb-1">
              <button type="button" className={buttonClasses("ghost", "sm")} onClick={() => preset(monthRange(0))}>
                این ماه
              </button>
              <button type="button" className={buttonClasses("ghost", "sm")} onClick={() => preset(monthRange(-1))}>
                ماه قبل
              </button>
              <button type="button" className={buttonClasses("ghost", "sm")} onClick={() => preset(yearRange())}>
                امسال
              </button>
              <button type="button" className={buttonClasses("ghost", "sm")} onClick={() => preset([addDays(currentBusinessDay(), -29), currentBusinessDay()])}>
                ۳۰ روز اخیر
              </button>
            </div>
          )}
        </div>
      )}

      {error && <Alert tone="error">{error}</Alert>}
      {loading && <Spinner className="h-7 w-7" />}
      {report === "vendors" && <VendorAging vendors={vendors} />}
      {report === "ledger" && !account && <p className="text-fg-muted">یک حساب انتخاب کنید.</p>}
      {!loading && !!data && report === "income" && <IncomeStatementReport d={data as IncomeStatement} />}
      {!loading && !!data && report === "balance" && <BalanceSheetReport d={data as BalanceSheet} />}
      {!loading && !!data && report === "trial" && <TrialBalanceReport d={data as TrialBalance} />}
      {!loading && !!data && report === "ledger" && <LedgerReport d={data as Ledger} />}
      {!loading && !!data && report === "sales" && <SalesReportView d={data as SalesReport} />}
      {!loading && !!data && report === "vat" && <VatReportView d={data as VatReport} />}
      {!loading && !!data && report === "cash" && <CashReport d={data as StatementLine[]} />}
    </div>
  );
}

function Export({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className={buttonClasses("ghost", "sm")}>
      خروجی CSV
    </button>
  );
}

function LineTable({ title, lines, total }: { title: string; lines: StatementLine[]; total: number }) {
  return (
    <section>
      <h3 className="mb-2 text-lg font-black">{title}</h3>
      <Table head={["کد", "حساب", "گروه", "مبلغ (تومان)"]} empty={lines.length === 0}>
        {lines.map((l) => (
          <tr key={l.code}>
            <td className={cell}>{fa(l.code)}</td>
            <td className={`${cell} font-bold`}>{l.name}</td>
            <td className={`${cell} text-fg-muted`}>{l.group}</td>
            <td className={cell}>{toman(l.amount_irr)}</td>
          </tr>
        ))}
        <tr className="bg-surface-2 font-black">
          <td className={cell} colSpan={3}>
            جمع
          </td>
          <td className={cell}>{toman(total)}</td>
        </tr>
      </Table>
    </section>
  );
}

function IncomeStatementReport({ d }: { d: IncomeStatement }) {
  const change = (now: number, before: number) => (before ? `${fa(Math.round(((now - before) / Math.abs(before)) * 100))}٪` : "—");
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Kpi label="درآمد" value={toman(d.total_revenue_irr)} note={`دوره قبل: ${toman(d.previous.total_revenue_irr)} (${change(d.total_revenue_irr, d.previous.total_revenue_irr)})`} tone="accent" />
        <Kpi label="هزینه" value={toman(d.total_expenses_irr)} note={`دوره قبل: ${toman(d.previous.total_expenses_irr)} (${change(d.total_expenses_irr, d.previous.total_expenses_irr)})`} />
        <Kpi label="سود (زیان) خالص" value={<span className={d.net_profit_irr < 0 ? "text-signal" : ""}>{toman(d.net_profit_irr)}</span>} note={`دوره قبل: ${toman(d.previous.net_profit_irr)}`} tone="dark" />
      </div>
      <div className="flex justify-end">
        <Export
          onClick={() =>
            downloadCsv(
              "income-statement",
              ["نوع", "کد", "حساب", "مبلغ (تومان)"],
              [...d.revenue.map((l) => ["درآمد", l.code, l.name, csvToman(l.amount_irr)]), ...d.expenses.map((l) => ["هزینه", l.code, l.name, csvToman(l.amount_irr)]), ["", "", "سود خالص", csvToman(d.net_profit_irr)]],
            )
          }
        />
      </div>
      <LineTable title="درآمدها" lines={d.revenue} total={d.total_revenue_irr} />
      <LineTable title="هزینه‌ها" lines={d.expenses} total={d.total_expenses_irr} />
    </div>
  );
}

function BalanceSheetReport({ d }: { d: BalanceSheet }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Kpi label="جمع دارایی‌ها" value={toman(d.total_assets_irr)} tone="dark" />
        <Kpi label="جمع بدهی‌ها" value={toman(d.total_liabilities_irr)} />
        <Kpi label="حقوق صاحبان سرمایه" value={toman(d.total_equity_irr)} note={`شامل سود (زیان) سال جاری: ${toman(d.current_earnings_irr)}`} tone="accent" />
      </div>
      {d.difference_irr !== 0 ? (
        <Alert tone="error">ترازنامه تراز نیست؛ اختلاف {toman(d.difference_irr)} تومان. لطفاً اسناد را بررسی کنید.</Alert>
      ) : (
        <Alert tone="success">ترازنامه تراز است: دارایی‌ها = بدهی‌ها + حقوق صاحبان سرمایه.</Alert>
      )}
      <div className="flex justify-end">
        <Export
          onClick={() =>
            downloadCsv(
              "balance-sheet",
              ["بخش", "کد", "حساب", "مبلغ (تومان)"],
              [
                ...d.assets.map((l) => ["دارایی", l.code, l.name, csvToman(l.amount_irr)]),
                ...d.liabilities.map((l) => ["بدهی", l.code, l.name, csvToman(l.amount_irr)]),
                ...d.equity.map((l) => ["حقوق صاحبان سرمایه", l.code, l.name, csvToman(l.amount_irr)]),
                ["حقوق صاحبان سرمایه", "", "سود (زیان) سال جاری", csvToman(d.current_earnings_irr)],
              ],
            )
          }
        />
      </div>
      <LineTable title="دارایی‌ها" lines={d.assets} total={d.total_assets_irr} />
      <LineTable title="بدهی‌ها" lines={d.liabilities} total={d.total_liabilities_irr} />
      <LineTable title="حقوق صاحبان سرمایه" lines={d.equity} total={d.total_equity_irr - d.current_earnings_irr} />
      <p className="font-bold">سود (زیان) سال جاری که هنوز به سود انباشته منتقل نشده: {toman(d.current_earnings_irr)} تومان</p>
    </div>
  );
}

function TrialBalanceReport({ d }: { d: TrialBalance }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className={`font-bold ${d.total_debit_irr === d.total_credit_irr ? "text-go" : "text-signal"}`}>
          {d.total_debit_irr === d.total_credit_irr ? "جمع بدهکار و بستانکار گردش برابر است." : "جمع گردش بدهکار و بستانکار برابر نیست!"}
        </p>
        <Export
          onClick={() =>
            downloadCsv(
              "trial-balance",
              ["کد", "حساب", "مانده اول بدهکار", "مانده اول بستانکار", "گردش بدهکار", "گردش بستانکار", "مانده پایان بدهکار", "مانده پایان بستانکار"],
              d.rows.map((r) => [r.code, r.name, csvToman(r.opening_debit_irr), csvToman(r.opening_credit_irr), csvToman(r.debit_irr), csvToman(r.credit_irr), csvToman(r.closing_debit_irr), csvToman(r.closing_credit_irr)]),
            )
          }
        />
      </div>
      <Table head={["کد", "حساب", "اول دوره (بد)", "اول دوره (بس)", "گردش بدهکار", "گردش بستانکار", "پایان (بد)", "پایان (بس)"]} empty={d.rows.length === 0}>
        {d.rows.map((r) => (
          <tr key={r.account_id}>
            <td className={cell}>{fa(r.code)}</td>
            <td className={`${cell} font-bold`}>{r.name}</td>
            <td className={cell}>{tomanOrDash(r.opening_debit_irr)}</td>
            <td className={cell}>{tomanOrDash(r.opening_credit_irr)}</td>
            <td className={cell}>{tomanOrDash(r.debit_irr)}</td>
            <td className={cell}>{tomanOrDash(r.credit_irr)}</td>
            <td className={cell}>{tomanOrDash(r.closing_debit_irr)}</td>
            <td className={cell}>{tomanOrDash(r.closing_credit_irr)}</td>
          </tr>
        ))}
        <tr className="bg-surface-2 font-black">
          <td className={cell} colSpan={4}>
            جمع
          </td>
          <td className={cell}>{toman(d.total_debit_irr)}</td>
          <td className={cell}>{toman(d.total_credit_irr)}</td>
          <td className={cell}>{toman(d.total_closing_debit_irr)}</td>
          <td className={cell}>{toman(d.total_closing_credit_irr)}</td>
        </tr>
      </Table>
    </div>
  );
}

function LedgerReport({ d }: { d: Ledger }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-bold">
          {fa(d.account.code)} · {d.account.name} — مانده اول: {toman(d.opening_irr)} · مانده پایان: {toman(d.closing_irr)} تومان (بدهکار مثبت)
        </p>
        <Export
          onClick={() =>
            downloadCsv(
              "ledger",
              ["سند", "تاریخ", "شرح", "نوع", "بدهکار", "بستانکار", "مانده"],
              d.lines.map((l) => [l.number, isoToJalali(l.date), l.description, SOURCE_LABEL[l.source] ?? l.source, csvToman(l.debit_irr), csvToman(l.credit_irr), csvToman(l.balance_irr)]),
            )
          }
        />
      </div>
      <Table head={["سند", "تاریخ", "شرح", "نوع", "بدهکار", "بستانکار", "مانده"]} empty={d.lines.length === 0}>
        {d.lines.map((l, index) => (
          <tr key={`${l.entry_id}-${index}`}>
            <td className={cell}>{fa(l.number)}</td>
            <td className={cell}>{fa(isoToJalali(l.date))}</td>
            <td className={`${cell} max-w-[20rem] truncate`} title={l.memo || l.description}>{l.memo || l.description}</td>
            <td className={cell}>{SOURCE_LABEL[l.source] ?? l.source}</td>
            <td className={cell}>{tomanOrDash(l.debit_irr)}</td>
            <td className={cell}>{tomanOrDash(l.credit_irr)}</td>
            <td className={`${cell} font-black`}>{toman(l.balance_irr)}</td>
          </tr>
        ))}
      </Table>
    </div>
  );
}

function SalesReportView({ d }: { d: SalesReport }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Kpi label="کل دریافتی" value={toman(d.received_irr)} tone="dark" />
        <Kpi label="آنلاین (درگاه)" value={toman(d.online_irr)} />
        <Kpi label="نقدی" value={toman(d.cash_irr)} />
        <Kpi label="کارت‌خوان" value={toman(d.card_irr)} />
        <Kpi label="درآمد شناسایی‌شده" value={toman(d.revenue_irr)} tone="accent" note="بعد از کسر مالیات و برگشتی" />
      </div>
      <div className="flex justify-end">
        <Export
          onClick={() =>
            downloadCsv(
              "sales",
              ["تاریخ", "آنلاین", "نقد", "کارتخوان", "انتقال", "جمع دریافتی", "درآمد"],
              d.days.map((x) => [isoToJalali(x.date), csvToman(x.online_irr), csvToman(x.cash_irr), csvToman(x.card_irr), csvToman(x.transfer_irr), csvToman(x.received_irr), csvToman(x.revenue_irr)]),
            )
          }
        />
      </div>
      <Table head={["روز", "آنلاین", "نقد", "کارت‌خوان", "انتقال", "جمع دریافتی", "درآمد"]} empty={d.days.length === 0}>
        {d.days.map((x) => (
          <tr key={x.date}>
            <td className={`${cell} font-bold`}>{fa(isoToJalali(x.date))}</td>
            <td className={cell}>{tomanOrDash(x.online_irr)}</td>
            <td className={cell}>{tomanOrDash(x.cash_irr)}</td>
            <td className={cell}>{tomanOrDash(x.card_irr)}</td>
            <td className={cell}>{tomanOrDash(x.transfer_irr)}</td>
            <td className={`${cell} font-black`}>{toman(x.received_irr)}</td>
            <td className={cell}>{tomanOrDash(x.revenue_irr)}</td>
          </tr>
        ))}
      </Table>
    </div>
  );
}

function VatReportView({ d }: { d: VatReport }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Kpi label="مانده از قبل" value={toman(d.opening_balance_irr)} note="مثبت یعنی بدهی به سازمان مالیاتی" />
      <Kpi label="مالیات فروش (دریافتی)" value={toman(d.collected_irr)} />
      <Kpi label="مالیات خرید (پرداختی)" value={toman(d.paid_irr)} />
      <Kpi label="خالص قابل پرداخت" value={toman(d.net_payable_irr)} tone="dark" note={d.net_payable_irr < 0 ? "منفی یعنی طلب از سازمان مالیاتی" : undefined} />
    </div>
  );
}

function CashReport({ d }: { d: StatementLine[] }): ReactNode {
  const total = d.reduce((s, l) => s + l.amount_irr, 0);
  return (
    <div className="space-y-4">
      <Kpi label="مجموع" value={toman(total)} tone="dark" />
      <Table head={["کد", "حساب", "مانده (تومان)"]} empty={d.length === 0}>
        {d.map((l) => (
          <tr key={l.code}>
            <td className={cell}>{fa(l.code)}</td>
            <td className={`${cell} font-bold`}>{l.name}</td>
            <td className={cell}>{toman(l.amount_irr)}</td>
          </tr>
        ))}
      </Table>
    </div>
  );
}

function VendorAging({ vendors }: { vendors: Vendor[] }) {
  const owing = vendors.filter((v) => v.owed_irr || v.advance_irr);
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Export
          onClick={() =>
            downloadCsv(
              "vendor-aging",
              ["تامین‌کننده", "بدهی", "تا ۳۰ روز", "۳۱ تا ۶۰", "۶۱ تا ۹۰", "بیش از ۹۰", "پیش‌پرداخت"],
              owing.map((v) => [v.name, csvToman(v.owed_irr), csvToman(v.age_0_30_irr), csvToman(v.age_31_60_irr), csvToman(v.age_61_90_irr), csvToman(v.age_over_90_irr), csvToman(v.advance_irr)]),
            )
          }
        />
      </div>
      <Table head={["تامین‌کننده", "بدهی", "تا ۳۰ روز", "۳۱ تا ۶۰", "۶۱ تا ۹۰", "بیش از ۹۰", "پیش‌پرداخت"]} empty={owing.length === 0}>
        {owing.map((v) => (
          <tr key={v.id}>
            <td className={`${cell} font-bold`}>{v.name}</td>
            <td className={`${cell} font-black`}>{toman(v.owed_irr)}</td>
            <td className={cell}>{tomanOrDash(v.age_0_30_irr)}</td>
            <td className={cell}>{tomanOrDash(v.age_31_60_irr)}</td>
            <td className={cell}>{tomanOrDash(v.age_61_90_irr)}</td>
            <td className={cell}>{tomanOrDash(v.age_over_90_irr)}</td>
            <td className={cell}>{tomanOrDash(v.advance_irr)}</td>
          </tr>
        ))}
      </Table>
    </div>
  );
}
