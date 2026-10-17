"use client";

import { useMemo, useState } from "react";
import { PaymentStatusBadge } from "@/components/ui/payment-status-badge";
import { CardIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { GATEWAY_NAME, dateTime, fa, jalali, number, toman } from "@/lib/format";
import { printReceipt } from "@/lib/ticket-tools";
import type { AccountPayment, PaymentStatusValue, Reservation } from "@/lib/types";
import { site } from "@/content/site";

type Filter = "all" | "paid" | "pending" | "failed";

const PENDING: PaymentStatusValue[] = ["created", "redirected", "verifying", "unknown", "refund_pending"];
const FAILED: PaymentStatusValue[] = ["failed", "expired", "reversed"];

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "همه" },
  { id: "paid", label: "موفق" },
  { id: "pending", label: "در حال بررسی" },
  { id: "failed", label: "ناموفق / برگشتی" },
];

function inFilter(p: AccountPayment, filter: Filter): boolean {
  if (filter === "paid") return p.status === "paid";
  if (filter === "pending") return PENDING.includes(p.status);
  if (filter === "failed") return FAILED.includes(p.status);
  return true;
}

/** The customer's payment history with bank reference numbers and printable receipts. */
export function AccountPayments({ payments, tickets }: { payments: AccountPayment[]; tickets: Reservation[] }) {
  const [filter, setFilter] = useState<Filter>("all");
  const ticketById = useMemo(() => new Map(tickets.map((t) => [t.id, t])), [tickets]);

  const paid = payments.filter((p) => p.status === "paid");
  const total = paid.reduce((sum, p) => sum + p.amount_toman, 0);
  const pending = payments.filter((p) => PENDING.includes(p.status)).length;
  const shown = payments.filter((p) => inFilter(p, filter));

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="مجموع پرداخت موفق" value={toman(total)} />
        <Stat label="تعداد پرداخت موفق" value={fa(paid.length)} />
        <Stat label="در حال بررسی" value={fa(pending)} />
      </div>

      {pending > 0 && (
        <Alert tone="warning">
          {fa(pending)} پرداخت هنوز نتیجه قطعی ندارد. اگر وجه از حساب شما کسر شده، سیستم خودکار آن را پیگیری می‌کند؛ لازم نیست دوباره پرداخت کنید. اگر
          تا چند ساعت روشن نشد، با پیست تماس بگیرید ({site.contact.phone.display}).
        </Alert>
      )}

      <div role="tablist" aria-label="فیلتر پرداخت‌ها" className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            role="tab"
            aria-selected={filter === f.id}
            onClick={() => setFilter(f.id)}
            className={`rounded-full px-4 py-2 text-sm font-bold ring-1 transition-colors ${
              filter === f.id ? "bg-accent text-ink ring-accent" : "bg-surface text-fg-muted ring-line-strong hover:text-fg"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {shown.length === 0 ? (
        <div className="panel-soft p-8 text-center">
          <CardIcon className="mx-auto h-10 w-10 text-fg-subtle" />
          <p className="mt-4 font-bold">{payments.length === 0 ? "هنوز پرداختی ثبت نشده است." : "پرداختی با این وضعیت نیست."}</p>
        </div>
      ) : (
        <ul className="divide-y divide-line rounded-3xl border border-line bg-surface">
          {shown.map((p) => {
            const ticket = p.reservation_id ? ticketById.get(p.reservation_id) : undefined;
            return (
              <li key={p.payment_id} className="flex flex-wrap items-center justify-between gap-4 px-5 py-5">
                <div className="min-w-0">
                  <p className="text-lg font-black">{toman(p.amount_toman)}</p>
                  <p className="mt-1 text-sm text-fg-muted">
                    {dateTime(p.created_at)} · {GATEWAY_NAME[p.gateway] ?? (p.gateway || "درگاه بانکی")}
                  </p>
                  {ticket && (
                    <p className="mt-1 text-sm text-fg-muted">
                      بلیت <span className="font-bold">{fa(ticket.ticket_number)}</span> · {ticket.weekday} {jalali(ticket.date_jalali)}، {fa(ticket.time)}
                    </p>
                  )}
                  {p.reference_id && (
                    <p className="mt-1 text-sm text-fg-muted">
                      شماره پیگیری: <span className="font-bold" dir="ltr">{fa(p.reference_id)}</span>
                    </p>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <PaymentStatusBadge status={p.status} />
                  {p.status === "paid" && (
                    <button
                      type="button"
                      onClick={() => printReceipt(p, ticket)}
                      className="rounded-full border-2 border-fg px-4 py-1.5 text-sm font-bold text-fg transition-colors hover:bg-fg hover:text-canvas"
                    >
                      رسید
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
      <p className="text-xs leading-7 text-fg-subtle">
        پرداخت‌ها فقط از درگاه رسمی بانک انجام می‌شود؛ اطلاعات کارت شما هیچ‌جا در این سایت ذخیره نمی‌شود. مبلغ‌ها به تومان ({number(10)} ریال = ۱ تومان).
      </p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel p-5">
      <p className="text-sm text-fg-muted">{label}</p>
      <p className="mt-2 text-xl font-black">{value}</p>
    </div>
  );
}
