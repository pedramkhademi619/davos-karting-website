"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Kpi, Pager, TabHeader, Table, cell } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { SearchIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { PAYMENT_STATUS, dateTime, fa, toLatinDigits, toman } from "@/lib/format";
import type { AdminPayment, PaymentStatusValue } from "@/lib/types";

const LIMIT = 50;
type PaymentPage = { items: AdminPayment[]; total: number; paid_total_toman: number };

const TONE: Partial<Record<PaymentStatusValue, string>> = {
  paid: "bg-go-soft text-[#064d29]",
  failed: "bg-signal-soft text-[#7a0600]",
  refund_pending: "bg-[#fff3c4] text-ink-soft",
  unknown: "bg-[#fff3c4] text-ink-soft",
};

/** Every payment attempt with its bank reference. Unclear ones are re-checked with the bank automatically every 2 minutes. */
export function PaymentsTab() {
  const { call } = useAdmin();
  const [status, setStatus] = useState<PaymentStatusValue | "">("");
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<PaymentPage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    call<PaymentPage>("/payments", { query: { status, q: submitted, offset, limit: LIMIT } })
      .then((result) => !cancelled && setPage(result))
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, status, submitted, offset]);

  function search(event: FormEvent) {
    event.preventDefault();
    setOffset(0);
    setSubmitted(toLatinDigits(query.trim()));
  }

  return (
    <div>
      <TabHeader
        title="پرداخت‌ها"
        lead="پرداخت‌های نامشخص هر دو دقیقه خودکار با بانک تطبیق داده می‌شوند؛ اگر پول کم شده ولی رزرو قابل قطعی شدن نبود، برگشت داده می‌شود."
        actions={
          <form onSubmit={search} className="flex flex-wrap items-center gap-2">
            <select
              className="field h-11 w-48"
              value={status}
              onChange={(e) => {
                setOffset(0);
                setStatus(e.target.value as PaymentStatusValue | "");
              }}
              aria-label="وضعیت"
            >
              <option value="">همه وضعیت‌ها</option>
              {Object.entries(PAYMENT_STATUS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <input className="field h-11 w-52" placeholder="کد پیگیری یا شماره سفارش" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="جستجو" />
            <button type="submit" className={buttonClasses("dark", "sm", "h-11")} aria-label="جستجو">
              <SearchIcon className="h-5 w-5" />
            </button>
          </form>
        }
      />
      {error && (
        <Alert tone="error" className="mb-6">
          {error}
        </Alert>
      )}
      {!page ? (
        <Spinner className="h-8 w-8" />
      ) : (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:w-2/3">
            <Kpi tone="dark" label="جمع پرداخت‌های موفق (همین فیلتر)" value={<span className="text-2xl">{toman(page.paid_total_toman)}</span>} />
            <Kpi label="تعداد" value={fa(page.total)} />
          </div>
          <Table head={["زمان", "مبلغ", "وضعیت", "درگاه", "شماره سفارش", "کد پیگیری بانک", "توضیح"]} empty={page.items.length === 0}>
            {page.items.map((p) => (
              <tr key={p.payment_id}>
                <td className={cell}>{dateTime(p.created_at)}</td>
                <td className={`${cell} font-bold`}>{toman(p.amount_toman)}</td>
                <td className={cell}>
                  <span className={`rounded-full px-3 py-1 text-xs font-bold ${TONE[p.status] ?? "bg-surface-2 text-fg-muted"}`}>{PAYMENT_STATUS[p.status]}</span>
                  {p.status === "paid" && !p.settled_at && <span className="mt-1 block text-xs text-fg-subtle">در انتظار تسویه</span>}
                </td>
                <td className={cell}>{p.gateway === "mellat" ? "بانک ملت" : p.gateway}</td>
                <td className={cell} dir="ltr">
                  {p.gateway_order_id ? fa(p.gateway_order_id) : "—"}
                </td>
                <td className={cell} dir="ltr">
                  {p.reference_id ? fa(p.reference_id) : "—"}
                </td>
                <td className={`${cell} max-w-[16rem] truncate text-xs text-fg-muted`}>{p.failure_reason ?? ""}</td>
              </tr>
            ))}
          </Table>
          <Pager offset={offset} limit={LIMIT} total={page.total} onChange={setOffset} />
        </>
      )}
    </div>
  );
}
