"use client";

import { useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Kpi } from "@/components/admin/admin-ui";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { toman, type AccountingDashboard } from "@/lib/accounting";
import { fa } from "@/lib/format";

const MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];

function monthLabel(key: string): string {
  const [year, month] = key.split("-").map(Number);
  return `${MONTHS[month - 1]} ${fa(year)}`;
}

/** The owner's money picture: what is in the till and bank, this month's result, and what is owed. */
export function AccountingDashboardView() {
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
  if (!data) return <Spinner className="h-8 w-8" />;

  const peak = Math.max(1, ...data.trend.flatMap((p) => [p.revenue_irr, p.expenses_irr]));

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label="موجودی نقد و بانک" value={`${toman(data.liquid_irr)}`} note="تومان؛ صندوق + بانک + کارت‌خوان + درگاه" tone="dark" />
        <Kpi label="درآمد این ماه" value={toman(data.month_revenue_irr)} note={`امروز: ${toman(data.today_revenue_irr)} تومان`} tone="accent" />
        <Kpi label="هزینه این ماه" value={toman(data.month_expenses_irr)} note="تومان" />
        <Kpi
          label="سود (زیان) این ماه"
          value={<span className={data.month_profit_irr < 0 ? "text-signal" : ""}>{toman(data.month_profit_irr)}</span>}
          note="تومان؛ درآمد منهای هزینه"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card title="کجا پول داریم">
          <dl className="space-y-3 text-sm">
            <Row label="صندوق" value={data.cash_irr} />
            <Row label="بانک" value={data.bank_irr} />
            <Row label="کارت‌خوان (تسویه‌نشده)" value={data.pos_irr} />
            <Row label="درگاه پرداخت (تسویه‌نشده)" value={data.gateway_irr} />
          </dl>
        </Card>
        <Card title="بدهی‌ها و تعهدات">
          <dl className="space-y-3 text-sm">
            <Row label="بدهی به تامین‌کنندگان" value={data.payables_irr} />
            <Row label="استرداد وجه به مشتریان" value={data.refunds_payable_irr} />
            <Row label="مالیات ارزش افزوده (پرداختنی)" value={data.vat_balance_irr} />
            <Row label="بلیت‌های پیش‌پرداخت‌شده (هنوز سانس‌نخورده)" value={data.unrecognized_advances_irr} />
          </dl>
        </Card>
        <Card title="بیشترین هزینه‌های این ماه">
          {data.top_expenses.length === 0 ? (
            <p className="text-sm text-fg-muted">هنوز هزینه‌ای ثبت نشده است.</p>
          ) : (
            <ul className="space-y-3 text-sm">
              {data.top_expenses.map((line) => (
                <li key={line.code} className="flex justify-between gap-3">
                  <span className="font-bold">{line.name}</span>
                  <span>{toman(line.amount_irr)}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card title="روند شش ماه اخیر (تومان)">
        <ul className="space-y-4">
          {data.trend.map((point) => (
            <li key={point.key}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="font-bold">{monthLabel(point.key)}</span>
                <span className={point.profit_irr < 0 ? "text-signal" : "text-fg-muted"}>سود: {toman(point.profit_irr)}</span>
              </div>
              <Bar label="درآمد" value={point.revenue_irr} peak={peak} className="bg-go" />
              <Bar label="هزینه" value={point.expenses_irr} peak={peak} className="bg-signal" />
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-fg-muted">{label}</dt>
      <dd className={`font-black ${value < 0 ? "text-signal" : ""}`}>{toman(value)}</dd>
    </div>
  );
}

function Bar({ label, value, peak, className }: { label: string; value: number; peak: number; className: string }) {
  return (
    <div className="mt-1 flex items-center gap-3">
      <span className="w-12 shrink-0 text-xs text-fg-subtle">{label}</span>
      <div className="h-3 flex-1 overflow-hidden rounded-full bg-surface-2">
        <div className={`h-full rounded-full ${className}`} style={{ width: `${Math.max(2, (value / peak) * 100)}%`, opacity: value === 0 ? 0.25 : 1 }} />
      </div>
      <span className="w-28 shrink-0 text-left text-xs">{toman(value)}</span>
    </div>
  );
}
