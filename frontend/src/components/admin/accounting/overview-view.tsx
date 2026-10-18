"use client";

import { useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Kpi } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { errorMessage } from "@/lib/api";
import { toman, type AccountingDashboard } from "@/lib/accounting";
import { fa } from "@/lib/format";
import { JALALI_MONTHS } from "@/lib/jalali";
import { PageSkeleton } from "@/components/ui/skeleton";

function monthLabel(key: string): string {
  const [year, month] = key.split("-").map(Number);
  return `${JALALI_MONTHS[month - 1]} ${fa(year)}`;
}

/** The owner's money at a glance: what is in the till and the bank, this month's result, and what is still owed back. */
export function OverviewView({ onPayRefunds }: { onPayRefunds: (owedIrr: number) => void }) {
  const { call } = useAdmin();
  const [data, setData] = useState<AccountingDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    call<AccountingDashboard>("/accounting/reports/dashboard")
      .then((d) => !cancelled && setData(d))
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call]);

  if (error) return <Alert tone="error">{error}</Alert>;
  if (!data) return <PageSkeleton variant="cards" />;

  const bank = data.bank_irr + data.pos_irr + data.gateway_irr;
  const peak = Math.max(1, ...data.trend.flatMap((p) => [p.revenue_irr, p.expenses_irr]));
  const topPeak = Math.max(1, ...data.top_expenses.map((l) => l.amount_irr));

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi
          label="سود این ماه"
          tone="dark"
          value={<span className={data.month_profit_irr < 0 ? "text-signal" : ""}>{toman(data.month_profit_irr)}</span>}
          note={`درآمد ${toman(data.month_revenue_irr)} − هزینه ${toman(data.month_expenses_irr)} تومان`}
        />
        <Kpi label="فروش امروز" tone="accent" value={toman(data.today_revenue_irr)} note="تومان" />
        <Kpi label="صندوق" value={toman(data.cash_irr)} note="تومان؛ پول نقد پیش شما" />
        <Kpi label="بانک" value={toman(bank)} note="تومان؛ فروش آنلاین و کارت‌خوان هم اینجا می‌نشیند" />
      </div>

      {data.refunds_payable_irr > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl bg-signal/10 p-5 ring-1 ring-signal/30">
          <div>
            <p className="font-black">{toman(data.refunds_payable_irr)} تومان استرداد به مشتری‌ها مانده</p>
            <p className="mt-1 text-sm text-fg-muted">پول بلیت‌های آنلاینِ لغوشده؛ وقتی به حساب مشتری برگرداندید، اینجا ثبتش کنید.</p>
          </div>
          <button type="button" onClick={() => onPayRefunds(data.refunds_payable_irr)} className={buttonClasses("primary", "md")}>
            ثبت پرداخت استرداد
          </button>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-5">
        <Card title="خرج این ماه کجا رفت" className="xl:col-span-2">
          {data.top_expenses.length === 0 ? (
            <p className="text-sm text-fg-muted">هنوز هزینه‌ای ثبت نشده است.</p>
          ) : (
            <ul className="space-y-4">
              {data.top_expenses.map((line) => (
                <li key={line.code}>
                  <div className="mb-1.5 flex justify-between gap-3 text-sm">
                    <span className="font-bold">{line.name}</span>
                    <span className="text-fg-muted">{toman(line.amount_irr)}</span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-surface-2">
                    <div className="h-full rounded-full bg-signal" style={{ width: `${Math.max(3, (line.amount_irr / topPeak) * 100)}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="شش ماه اخیر" className="xl:col-span-3">
          <ul className="space-y-4">
            {data.trend.map((point) => (
              <li key={point.key}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-bold">{monthLabel(point.key)}</span>
                  <span className={point.profit_irr < 0 ? "font-bold text-signal" : "text-fg-muted"}>سود {toman(point.profit_irr)}</span>
                </div>
                <Bar label="درآمد" value={point.revenue_irr} peak={peak} className="bg-go" />
                <Bar label="هزینه" value={point.expenses_irr} peak={peak} className="bg-signal" />
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}

function Bar({ label, value, peak, className }: { label: string; value: number; peak: number; className: string }) {
  return (
    <div className="mt-1 flex items-center gap-3">
      <span className="w-12 shrink-0 text-xs text-fg-subtle">{label}</span>
      <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-2">
        <div className={`h-full rounded-full ${className}`} style={{ width: `${Math.max(2, (value / peak) * 100)}%`, opacity: value === 0 ? 0.25 : 1 }} />
      </div>
      <span className="w-24 shrink-0 text-left text-xs sm:w-28">{toman(value)}</span>
    </div>
  );
}
