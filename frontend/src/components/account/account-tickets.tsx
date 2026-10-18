"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useCountdown } from "@/components/booking/use-countdown";
import { buttonClasses } from "@/components/button-link";
import { CalendarIcon, SearchIcon, TicketIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/ui/status-badge";
import { site } from "@/content/site";
import { api, errorMessage } from "@/lib/api";
import { clock, dateTime, fa, jalali, karts, toLatinDigits, toman } from "@/lib/format";
import { goToGateway } from "@/lib/gateway";
import { downloadCalendarEvent, printTicket } from "@/lib/ticket-tools";
import type { AccountPayment, Me, Reservation, StartPayment } from "@/lib/types";
import { isOpenTicket } from "./use-account-data";

type Filter = "all" | "upcoming" | "past" | "cancelled";

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "همه" },
  { id: "upcoming", label: "پیش رو" },
  { id: "past", label: "گذشته" },
  { id: "cancelled", label: "لغو / منقضی" },
];

function matches(ticket: Reservation, filter: Filter): boolean {
  if (filter === "upcoming") return isOpenTicket(ticket);
  if (filter === "past") return ticket.status === "attended";
  if (filter === "cancelled") return ticket.status === "cancelled" || ticket.status === "expired";
  return true;
}

/** Every ticket the customer ever made: filter, search by ticket number or code, pay or release a held one. */
export function AccountTickets({
  tickets,
  payments,
  me,
  onChanged,
}: {
  tickets: Reservation[];
  payments: AccountPayment[];
  me: Me;
  onChanged: () => void;
}) {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");

  const paymentFor = useMemo(() => {
    const map = new Map<string, AccountPayment>();
    for (const p of payments) if (p.status === "paid" && p.reservation_id) map.set(p.reservation_id, p);
    return map;
  }, [payments]);

  const counts = useMemo(
    () => Object.fromEntries(FILTERS.map((f) => [f.id, tickets.filter((t) => matches(t, f.id)).length])) as Record<Filter, number>,
    [tickets],
  );

  const needle = toLatinDigits(query).trim().toLowerCase();
  const shown = tickets.filter(
    (t) => matches(t, filter) && (!needle || String(t.ticket_number).includes(needle) || t.code.toLowerCase().includes(needle)),
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div role="tablist" aria-label="فیلتر بلیت‌ها" className="flex flex-wrap gap-2">
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
              {f.label} <span className="opacity-70">{fa(counts[f.id])}</span>
            </button>
          ))}
        </div>
        <div className="relative w-full sm:w-64">
          <SearchIcon className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-fg-subtle" />
          <input
            className="field pr-12"
            placeholder="شماره بلیت یا کد رزرو"
            aria-label="جستجوی بلیت"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            inputMode="search"
          />
        </div>
      </div>

      {shown.length === 0 ? (
        <div className="panel-soft p-8 text-center">
          <TicketIcon className="mx-auto h-10 w-10 text-fg-subtle" />
          <p className="mt-4 font-bold">{tickets.length === 0 ? "هنوز بلیتی ندارید." : "بلیتی با این مشخصات پیدا نشد."}</p>
          {tickets.length === 0 && (
            <Link href={site.booking.href} className={buttonClasses("primary", "md", "mt-5")}>
              اولین رزرو
            </Link>
          )}
        </div>
      ) : (
        <ul className="space-y-4">
          {shown.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} payment={paymentFor.get(ticket.id)} me={me} onChanged={onChanged} />
          ))}
        </ul>
      )}
    </div>
  );
}

export function TicketCard({
  ticket,
  payment,
  me,
  onChanged,
}: {
  ticket: Reservation;
  payment?: AccountPayment;
  me: Me;
  onChanged: () => void;
}) {
  const left = useCountdown(ticket.status === "held" ? ticket.hold_expires_at : null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const held = ticket.status === "held";
  const expired = held && left !== null && left <= 0;
  const live = isOpenTicket(ticket);

  async function pay() {
    setBusy(true);
    setError(null);
    try {
      goToGateway(await api<StartPayment>(`/reservations/${ticket.id}/pay`, { method: "POST", csrf: me.csrf_token }));
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  async function release() {
    setBusy(true);
    setError(null);
    try {
      await api<void>(`/reservations/${ticket.id}`, { method: "DELETE", csrf: me.csrf_token });
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function copyNumber() {
    try {
      await navigator.clipboard.writeText(String(ticket.ticket_number));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      // clipboard blocked: the number is on screen anyway
    }
  }

  const muted = live ? "text-on-carbon-muted" : "text-fg-muted";
  const tool = live ? buttonClasses("ghost-light", "sm") : buttonClasses("ghost", "sm");

  return (
    <li className={`overflow-hidden rounded-[1.75rem] ${live ? "carbon" : "panel"}`}>
      <div className="flex flex-wrap items-start justify-between gap-5 p-6">
        <div>
          <StatusBadge status={ticket.status} />
          <p className="mt-3 text-2xl font-black">
            {ticket.weekday} {jalali(ticket.date_jalali)}، ساعت {fa(ticket.time)}
          </p>
          <p className={`mt-1 ${muted}`}>
            {karts(ticket.single_count, ticket.double_count)} · {fa(ticket.people)} نفر · {toman(ticket.amount_toman)}
          </p>
        </div>
        <div className="text-left">
          <p className={`text-xs ${muted}`}>شماره بلیت</p>
          <p className={`race-number mt-1 text-4xl font-black tracking-wider ${live ? "text-accent" : ""}`} dir="ltr">
            {fa(ticket.ticket_number)}
          </p>
        </div>
      </div>

      {held && (
        <div className="space-y-3 border-t border-carbon-line p-6">
          {error && <Alert tone="error">{error}</Alert>}
          {expired ? (
            <p className={`text-sm ${muted}`}>زمان پرداخت این رزرو تمام شده است.</p>
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              <button type="button" onClick={pay} disabled={busy} className={buttonClasses("primary", "md")}>
                {busy ? <Spinner /> : `پرداخت ${toman(ticket.amount_toman)}`}
              </button>
              <button type="button" onClick={release} disabled={busy} className={buttonClasses("ghost-light", "md")}>
                انصراف
              </button>
              {left !== null && (
                <span className={`text-sm ${muted}`}>
                  {fa(Math.floor(left / 60))} دقیقه و {fa(left % 60)} ثانیه تا پایان نگه‌داری
                </span>
              )}
            </div>
          )}
        </div>
      )}

      <div className={`flex flex-wrap items-center gap-2 border-t px-6 py-4 ${live ? "border-carbon-line" : "border-line"}`}>
        {ticket.status === "confirmed" && (
          <button type="button" onClick={() => downloadCalendarEvent(ticket)} className={tool}>
            <CalendarIcon className="h-4 w-4" />
            افزودن به تقویم
          </button>
        )}
        {ticket.status === "confirmed" && (
          <button type="button" onClick={() => printTicket(ticket)} className={tool}>
            چاپ بلیت
          </button>
        )}
        <button type="button" onClick={copyNumber} className={tool}>
          {copied ? "کپی شد" : "کپی شماره بلیت"}
        </button>
        <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open} className={`${tool} mr-auto`}>
          {open ? "بستن جزئیات" : "جزئیات"}
        </button>
      </div>

      {open && (
        <dl className={`grid gap-x-8 gap-y-3 border-t px-6 py-5 text-sm sm:grid-cols-2 ${live ? "border-carbon-line" : "border-line"}`}>
          <Detail label="کد رزرو" value={ticket.code} ltr muted={muted} />
          <Detail label="نام روی بلیت" value={ticket.contact_name || "—"} muted={muted} />
          <Detail label="ثبت رزرو" value={dateTime(ticket.created_at)} muted={muted} />
          {ticket.confirmed_at && <Detail label="تایید قطعی" value={dateTime(ticket.confirmed_at)} muted={muted} />}
          <Detail label="روش ثبت" value={ticket.source === "staff" ? "ثبت حضوری در پیست" : "رزرو آنلاین"} muted={muted} />
          {payment?.reference_id && <Detail label="شماره پیگیری پرداخت" value={fa(payment.reference_id)} ltr muted={muted} />}
          {ticket.hold_expires_at && held && <Detail label="مهلت پرداخت تا" value={clock(ticket.hold_expires_at)} muted={muted} />}
          {ticket.cancel_reason && <Detail label="دلیل لغو" value={ticket.cancel_reason} muted={muted} />}
          {ticket.confirmed_late && (
            <div className="sm:col-span-2">
              <Alert tone="info">پرداخت این بلیت بعد از پایان مهلت انجام شد و چون جا خالی بود، رزرو شما حفظ شد.</Alert>
            </div>
          )}
        </dl>
      )}
    </li>
  );
}

function Detail({ label, value, ltr, muted }: { label: string; value: string; ltr?: boolean; muted: string }) {
  return (
    <div>
      <dt className={`text-xs ${muted}`}>{label}</dt>
      <dd className="mt-0.5 font-bold" dir={ltr ? "ltr" : undefined} style={ltr ? { textAlign: "right" } : undefined}>
        {value}
      </dd>
    </div>
  );
}
