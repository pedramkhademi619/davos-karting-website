"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, TabHeader, Table, cell } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { SearchIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/ui/status-badge";
import { errorMessage } from "@/lib/api";
import { fa, jalali, karts, mobile, toLatinDigits, toman } from "@/lib/format";
import { addDays, currentBusinessDay, isoToJalali, parseJalali } from "@/lib/jalali";
import type { DayAvailability, Page, Reservation } from "@/lib/types";

/** One business day at a glance: the seat board, the day's reservations, and counter sales entered by staff. */
export function ReservationsTab() {
  const { call } = useAdmin();
  const [date, setDate] = useState(() => currentBusinessDay());
  const [dateInput, setDateInput] = useState(() => isoToJalali(currentBusinessDay()));
  const [board, setBoard] = useState<DayAvailability | null>(null);
  const [list, setList] = useState<Reservation[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedTime, setSelectedTime] = useState<string>("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Reservation[] | null>(null);
  const [version, setVersion] = useState(0);

  const reload = useCallback(() => setVersion((v) => v + 1), []);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      call<DayAvailability>("/reservations/board", { query: { date } }),
      call<Page<Reservation>>("/reservations", { query: { date_from: date, date_to: date, limit: 200 } }),
    ])
      .then(([day, page]) => {
        if (cancelled) return;
        setBoard(day);
        setList([...page.items].sort((a, b) => a.starts_at.localeCompare(b.starts_at)));
        setError(null);
      })
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, date, version]);

  function goTo(next: string) {
    setDate(next);
    setDateInput(isoToJalali(next));
    setBoard(null);
    setList(null);
    setSelectedTime("");
  }

  function onDateInput(event: FormEvent) {
    event.preventDefault();
    const parsed = parseJalali(dateInput);
    if (parsed) goTo(parsed);
    else setError("تاریخ را به شکل ۱۴۰۵/۰۷/۰۴ وارد کنید.");
  }

  async function search(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) {
      setResults(null);
      return;
    }
    try {
      const page = await call<Page<Reservation>>("/reservations", { query: { q: toLatinDigits(query.trim()), limit: 50 } });
      setResults(page.items);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  const today = currentBusinessDay();
  const totals = useMemo(() => {
    const active = (list ?? []).filter((r) => r.status === "confirmed" || r.status === "attended" || r.status === "held");
    return { count: active.length, karts: active.reduce((n, r) => n + r.single_count + r.double_count, 0) };
  }, [list]);

  return (
    <div>
      <TabHeader
        title="رزروها و سانس‌ها"
        lead="هر فروش حضوری را اینجا ثبت کنید تا همان خودروها آنلاین فروخته نشوند (سامانه باجه با سایت همگام نیست)."
        actions={
          <form onSubmit={search} className="flex items-center gap-2">
            <input
              className="field h-11 w-56"
              placeholder="کد رزرو، موبایل یا نام"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="جستجوی رزرو"
            />
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

      {results && (
        <Card title={`نتیجه جستجو (${fa(results.length)})`} className="mb-6">
          <ReservationRows items={results} onChanged={reload} showDate />
          <button type="button" className="mt-4 text-sm font-bold underline" onClick={() => setResults(null)}>
            بستن نتیجه
          </button>
        </Card>
      )}

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <button type="button" className={buttonClasses("ghost", "sm")} onClick={() => goTo(addDays(date, -1))}>
          روز قبل
        </button>
        <button type="button" className={buttonClasses(date === today ? "dark" : "ghost", "sm")} onClick={() => goTo(today)}>
          امروز
        </button>
        <button type="button" className={buttonClasses("ghost", "sm")} onClick={() => goTo(addDays(date, 1))}>
          روز بعد
        </button>
        <form onSubmit={onDateInput} className="flex items-center gap-2">
          <input className="field h-10 w-36 text-center" dir="ltr" value={fa(dateInput)} onChange={(e) => setDateInput(e.target.value)} aria-label="تاریخ (شمسی)" />
          <button type="submit" className={buttonClasses("dark", "sm")}>
            برو
          </button>
        </form>
        {board && (
          <span className="text-sm font-bold text-fg-muted">
            {board.weekday} {jalali(board.date_jalali)}
            {board.is_holiday && " · تعطیل"}
            {board.is_closed && " · بدون رزرو آنلاین"} · {fa(totals.count)} رزرو، {fa(totals.karts)} خودرو
          </span>
        )}
      </div>

      <div className="grid gap-6 xl:grid-cols-12">
        <div className="space-y-6 xl:col-span-8">
          <Card title="جدول سانس‌ها">
            {!board ? (
              <Spinner className="h-7 w-7" />
            ) : (
              <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 lg:grid-cols-8">
                {board.sessions.map((s) => {
                  const soldOut = s.singles_left + s.doubles_left === 0;
                  const active = selectedTime === s.time;
                  return (
                    <button
                      key={s.time}
                      type="button"
                      onClick={() => setSelectedTime(s.time)}
                      className={`rounded-xl border-2 p-2 text-center transition-colors ${
                        active ? "carbon border-accent" : soldOut ? "border-signal/40 bg-signal-soft" : "border-line bg-surface hover:border-fg"
                      }`}
                    >
                      <span className="block text-base font-black">{fa(s.time)}</span>
                      <span className={`block text-[0.7rem] font-bold ${active ? "text-on-carbon-muted" : "text-fg-muted"}`}>
                        {fa(s.singles_left)}/{fa(s.single_capacity)} · {fa(s.doubles_left)}/{fa(s.double_capacity)}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
            <p className="mt-3 text-xs text-fg-subtle">عددها: تک‌نفره خالی/کل · دونفره خالی/کل. روی سانس بزنید تا در فرم ثبت حضوری انتخاب شود.</p>
          </Card>

          <Card title="رزروهای این روز">
            {!list ? <Spinner className="h-7 w-7" /> : <ReservationRows items={list} onChanged={reload} />}
          </Card>
        </div>

        <div className="xl:col-span-4">
          <StaffEntry board={board} time={selectedTime} onTime={setSelectedTime} date={date} onCreated={reload} />
        </div>
      </div>
    </div>
  );
}

function ReservationRows({ items, onChanged, showDate = false }: { items: Reservation[]; onChanged: () => void; showDate?: boolean }) {
  const { call } = useAdmin();
  const [busyId, setBusyId] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function act(id: string, path: string, body?: unknown) {
    setBusyId(id);
    setError(null);
    try {
      await call<Reservation>(`/reservations/${id}/${path}`, { method: "POST", body });
      setCancelling(null);
      setReason("");
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      {error && (
        <Alert tone="error" className="mb-4">
          {error}
        </Alert>
      )}
      <Table head={["کد", showDate ? "روز و ساعت" : "ساعت", "نام / موبایل", "خودرو", "مبلغ", "وضعیت", "منبع", ""]} empty={items.length === 0}>
        {items.map((r) => (
          <tr key={r.id} className="hover:bg-surface-2/60">
            <td className={`${cell} race-number text-xs font-bold`} dir="ltr">
              {r.code}
            </td>
            <td className={`${cell} font-bold`}>{showDate ? `${jalali(r.date_jalali)} ${fa(r.time)}` : fa(r.time)}</td>
            <td className={cell}>
              <span className="block font-bold">{r.contact_name || "—"}</span>
              <span className="block text-xs text-fg-muted" dir="ltr">
                {r.contact_mobile ? mobile(r.contact_mobile) : ""}
              </span>
              {r.note && <span className="block max-w-[14rem] truncate text-xs text-fg-subtle">{r.note}</span>}
            </td>
            <td className={cell}>{karts(r.single_count, r.double_count)}</td>
            <td className={cell}>{toman(r.amount_toman)}</td>
            <td className={cell}>
              <StatusBadge status={r.status} />
              {r.cancel_reason && <span className="mt-1 block max-w-[12rem] truncate text-xs text-fg-subtle">{r.cancel_reason}</span>}
            </td>
            <td className={cell}>{r.source === "online" ? "آنلاین" : "حضوری"}</td>
            <td className={cell}>
              {cancelling === r.id ? (
                <span className="flex items-center gap-2">
                  <input className="field h-9 w-40 text-xs" placeholder="دلیل لغو" value={reason} onChange={(e) => setReason(e.target.value)} />
                  <button type="button" disabled={busyId === r.id} className={buttonClasses("signal", "sm", "h-9")} onClick={() => act(r.id, "cancel", { reason })}>
                    تایید لغو
                  </button>
                  <button type="button" className="text-xs font-bold underline" onClick={() => setCancelling(null)}>
                    بی‌خیال
                  </button>
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  {r.status === "confirmed" && (
                    <button type="button" disabled={busyId === r.id} className={buttonClasses("dark", "sm", "h-9")} onClick={() => act(r.id, "attended")}>
                      حاضر شد
                    </button>
                  )}
                  {(r.status === "confirmed" || r.status === "held") && (
                    <button type="button" className="text-xs font-bold text-signal underline" onClick={() => setCancelling(r.id)}>
                      لغو
                    </button>
                  )}
                </span>
              )}
            </td>
          </tr>
        ))}
      </Table>
      {items.some((r) => r.status === "confirmed" && r.source === "online") && (
        <p className="mt-3 text-xs text-fg-subtle">لغو رزرو آنلاینِ پرداخت‌شده، مبلغ را خودکار برنمی‌گرداند؛ بازپرداخت را از پنل بانک انجام دهید.</p>
      )}
    </>
  );
}

function StaffEntry({
  board,
  time,
  onTime,
  date,
  onCreated,
}: {
  board: DayAvailability | null;
  time: string;
  onTime: (time: string) => void;
  date: string;
  onCreated: () => void;
}) {
  const { call } = useAdmin();
  const [singles, setSingles] = useState(1);
  const [doubles, setDoubles] = useState(0);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [note, setNote] = useState("");
  const [amount, setAmount] = useState("");
  const [overbook, setOverbook] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  const suggested = board ? singles * board.single_price_toman + doubles * board.double_price_toman : 0;

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!time) {
      setMessage({ tone: "error", text: "اول سانس را از جدول انتخاب کنید." });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const created = await call<Reservation>("/reservations", {
        method: "POST",
        body: {
          date,
          time,
          single_count: singles,
          double_count: doubles,
          contact_name: name.trim(),
          contact_mobile: toLatinDigits(phone.trim()),
          note: note.trim(),
          amount_toman: amount.trim() ? Number(toLatinDigits(amount).replace(/\D/g, "")) : suggested,
          allow_overbooking: overbook,
        },
      });
      setMessage({ tone: "success", text: `ثبت شد: ${created.code}` });
      setName("");
      setPhone("");
      setNote("");
      setAmount("");
      setOverbook(false);
      onCreated();
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="carbon space-y-4 rounded-[1.75rem] p-6 xl:sticky xl:top-6">
      <h2 className="text-lg font-black">ثبت فروش حضوری</h2>
      <div>
        <label className="label text-on-carbon-muted" htmlFor="entry-time">
          سانس
        </label>
        <select id="entry-time" className="field field-dark" value={time} onChange={(e) => onTime(e.target.value)}>
          <option value="">انتخاب کنید</option>
          {board?.sessions.map((s) => (
            <option key={s.time} value={s.time}>
              {fa(s.time)} — خالی: {fa(s.singles_left)} تک، {fa(s.doubles_left)} دو
            </option>
          ))}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label text-on-carbon-muted" htmlFor="entry-singles">
            تک‌نفره
          </label>
          <input id="entry-singles" type="number" min={0} max={50} className="field field-dark" value={singles} onChange={(e) => setSingles(Math.max(0, Number(e.target.value)))} />
        </div>
        <div>
          <label className="label text-on-carbon-muted" htmlFor="entry-doubles">
            دونفره
          </label>
          <input id="entry-doubles" type="number" min={0} max={50} className="field field-dark" value={doubles} onChange={(e) => setDoubles(Math.max(0, Number(e.target.value)))} />
        </div>
      </div>
      <div>
        <label className="label text-on-carbon-muted" htmlFor="entry-name">
          نام مشتری
        </label>
        <input id="entry-name" className="field field-dark" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} />
      </div>
      <div>
        <label className="label text-on-carbon-muted" htmlFor="entry-mobile">
          موبایل (برای پیامک اختیاری)
        </label>
        <input id="entry-mobile" dir="ltr" className="field field-dark" value={phone} onChange={(e) => setPhone(e.target.value)} maxLength={16} />
      </div>
      <div>
        <label className="label text-on-carbon-muted" htmlFor="entry-amount">
          مبلغ دریافتی (تومان)
        </label>
        <input
          id="entry-amount"
          dir="ltr"
          inputMode="numeric"
          className="field field-dark"
          placeholder={String(suggested)}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
        <p className="mt-1 text-xs text-on-carbon-muted">خالی بماند = {toman(suggested)} (قیمت همین روز)</p>
      </div>
      <div>
        <label className="label text-on-carbon-muted" htmlFor="entry-note">
          یادداشت
        </label>
        <textarea id="entry-note" className="field field-dark" value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} />
      </div>
      <label className="flex items-start gap-3 text-sm text-on-carbon-muted">
        <input type="checkbox" checked={overbook} onChange={(e) => setOverbook(e.target.checked)} className="mt-1 h-4 w-4 accent-[#ffc400]" />
        اجازه ثبت بیش از ظرفیت (فقط وقتی واقعاً خودرو دارید)
      </label>
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      <button type="submit" disabled={busy || singles + doubles === 0} className={buttonClasses("primary", "lg", "w-full")}>
        {busy ? <Spinner /> : "ثبت و بستن جا"}
      </button>
    </form>
  );
}
