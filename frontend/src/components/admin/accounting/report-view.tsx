"use client";

import { useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Kpi } from "@/components/admin/admin-ui";
import { MonthStepper } from "@/components/admin/accounting/month-stepper";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import {
  csvToman,
  downloadCsv,
  monthBounds,
  monthName,
  monthOf,
  toman,
  type IncomeStatement,
  type JalaliMonth,
  type SalesReport,
  type StatementLine,
} from "@/lib/accounting";
import { fa } from "@/lib/format";
import { currentBusinessDay } from "@/lib/jalali";

/** Change against the previous month, as "+۱۲٪" / "−۵٪" (nothing when there is no previous month to compare with). */
function change(now: number, before: number): string | null {
  if (!before) return null;
  const percent = Math.round(((now - before) / Math.abs(before)) * 100);
  return `${percent > 0 ? "+" : percent < 0 ? "−" : ""}${fa(Math.abs(percent))}٪ نسبت به ماه قبل`;
}

/** One month's profit and loss in categories, compared with the month before, with a CSV for the accountant. */
export function ReportView() {
  const { call } = useAdmin();
  const [month, setMonth] = useState<JalaliMonth>(() => monthOf(currentBusinessDay()));
  const [loaded, setLoaded] = useState<{ key: string; statement: IncomeStatement; sales: SalesReport } | null>(null);
  const key = `${month.year}-${month.month}`;
  const data = loaded?.key === key ? loaded : null; // a month still loading shows the spinner, not last month's numbers
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const [from, to] = monthBounds(month);
    Promise.all([
      call<IncomeStatement>("/accounting/reports/income-statement", { query: { from, to } }),
      call<SalesReport>("/accounting/reports/sales", { query: { from, to } }),
    ])
      .then(([statement, sales]) => {
        if (cancelled) return;
        setLoaded({ key: `${month.year}-${month.month}`, statement, sales });
        setError(null);
      })
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, month]);

  function exportCsv() {
    if (!data) return;
    const { statement } = data;
    const rows: (string | number)[][] = [
      ...statement.revenue.map((l) => ["درآمد", l.name, csvToman(l.amount_irr)]),
      ["درآمد", "جمع درآمد", csvToman(statement.total_revenue_irr)],
      ...statement.expenses.map((l) => ["هزینه", l.name, csvToman(l.amount_irr)]),
      ["هزینه", "جمع هزینه", csvToman(statement.total_expenses_irr)],
      ["", "سود (زیان)", csvToman(statement.net_profit_irr)],
    ];
    downloadCsv(`سود-و-زیان-${monthName(month)}`, ["نوع", "دسته", "مبلغ (تومان)"], rows);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <MonthStepper month={month} onChange={setMonth} />
        <button type="button" onClick={exportCsv} disabled={!data} className={buttonClasses("ghost", "sm")}>
          خروجی اکسل (CSV)
        </button>
      </div>
      {error && <Alert tone="error">{error}</Alert>}
      {!data ? (
        !error && <Spinner className="h-8 w-8" />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Kpi
              label="سود (زیان)"
              tone="dark"
              value={<span className={data.statement.net_profit_irr < 0 ? "text-signal" : ""}>{toman(data.statement.net_profit_irr)}</span>}
              note={change(data.statement.net_profit_irr, data.statement.previous.net_profit_irr) ?? "تومان"}
            />
            <Kpi
              label="درآمد"
              value={toman(data.statement.total_revenue_irr)}
              note={change(data.statement.total_revenue_irr, data.statement.previous.total_revenue_irr) ?? "تومان"}
            />
            <Kpi
              label="هزینه"
              value={toman(data.statement.total_expenses_irr)}
              note={change(data.statement.total_expenses_irr, data.statement.previous.total_expenses_irr) ?? "تومان"}
            />
          </div>

          {data.sales.received_irr > 0 && (
            <Card title="فروش بلیت از کجا آمد">
              <div className="grid gap-3 sm:grid-cols-3">
                <Channel label="آنلاین (سایت)" value={data.sales.online_irr} total={data.sales.received_irr} />
                <Channel label="حضوری، نقد" value={data.sales.cash_irr} total={data.sales.received_irr} />
                <Channel label="حضوری، کارت" value={data.sales.card_irr} total={data.sales.received_irr} />
              </div>
            </Card>
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            <Lines title="درآمدها" lines={data.statement.revenue} total={data.statement.total_revenue_irr} tone="bg-go" />
            <Lines title="هزینه‌ها" lines={data.statement.expenses} total={data.statement.total_expenses_irr} tone="bg-signal" />
          </div>
        </>
      )}
    </div>
  );
}

function Channel({ label, value, total }: { label: string; value: number; total: number }) {
  return (
    <div className="rounded-2xl bg-surface-2 p-4">
      <p className="text-sm text-fg-muted">{label}</p>
      <p className="mt-1 text-xl font-black">{toman(value)}</p>
      <p className="text-xs text-fg-subtle">{fa(Math.round((value / total) * 100))}٪ فروش</p>
    </div>
  );
}

function Lines({ title, lines, total, tone }: { title: string; lines: StatementLine[]; total: number; tone: string }) {
  const shown = lines.filter((l) => l.amount_irr !== 0).sort((a, b) => b.amount_irr - a.amount_irr);
  const peak = Math.max(1, ...shown.map((l) => Math.abs(l.amount_irr)));
  return (
    <Card title={title}>
      {shown.length === 0 ? (
        <p className="text-sm text-fg-muted">چیزی ثبت نشده است.</p>
      ) : (
        <ul className="space-y-4">
          {shown.map((line) => (
            <li key={line.code}>
              <div className="mb-1.5 flex justify-between gap-3 text-sm">
                <span className="font-bold">{line.name}</span>
                <span className={line.amount_irr < 0 ? "text-signal" : "text-fg-muted"}>{toman(line.amount_irr)}</span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-surface-2">
                <div className={`h-full rounded-full ${tone}`} style={{ width: `${Math.max(3, (Math.abs(line.amount_irr) / peak) * 100)}%` }} />
              </div>
            </li>
          ))}
          <li className="flex justify-between border-t border-line pt-3 font-black">
            <span>جمع</span>
            <span>{toman(total)}</span>
          </li>
        </ul>
      )}
    </Card>
  );
}
