"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { OtpLogin } from "@/components/auth/otp-login";
import { DayStrip } from "@/components/booking/day-strip";
import { HoldTicket } from "@/components/booking/hold-ticket";
import { KartStepper } from "@/components/booking/kart-stepper";
import { SessionGrid } from "@/components/booking/session-grid";
import { buttonClasses } from "@/components/button-link";
import { PhoneIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { site } from "@/content/site";
import { ApiError, api, errorMessage } from "@/lib/api";
import { fa, jalali, karts, toman } from "@/lib/format";
import { goToGateway } from "@/lib/gateway";
import { SPLIT_HOSTS, hrefFor } from "@/lib/urls";
import type { BookingCalendar, DayAvailability, Me, Reservation, StartPayment } from "@/lib/types";
import { useCustomer } from "@/lib/use-customer";

const REFRESH_MS = 20_000; // seat counts are refreshed while the customer is choosing
const JUNIOR_DAYS = new Set(["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه"]);

type Phase = "choose" | "login" | "held";

/**
 * Online booking, like buying cinema tickets: pick a day and a session on the live seat map, choose single and double karts,
 * sign in with an SMS code, hold the karts, and pay at the bank. Prices and the total always come from the API; the page
 * only shows them.
 */
export function BookingApp() {
  const { state: customer, signedIn } = useCustomer();
  const [calendar, setCalendar] = useState<BookingCalendar | null>(null);
  const [calendarError, setCalendarError] = useState<string | null>(null);
  const [date, setDate] = useState<string | null>(null);
  const [day, setDay] = useState<DayAvailability | null>(null);
  const [dayError, setDayError] = useState<string | null>(null);
  const [time, setTime] = useState<string | null>(null);
  const [singlesWanted, setSingles] = useState(0);
  const [doublesWanted, setDoubles] = useState(0);
  const [contactName, setContactName] = useState("");
  const [phase, setPhase] = useState<Phase>("choose");
  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [pendingHold, setPendingHold] = useState<Reservation | null>(null);
  const [busy, setBusy] = useState<"hold" | "pay" | "release" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dayVersion, setDayVersion] = useState(0);
  const reloadDay = () => setDayVersion((v) => v + 1);

  // ---- data ----------------------------------------------------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;
    api<BookingCalendar>("/reservations/calendar")
      .then((result) => {
        if (cancelled) return;
        setCalendar(result);
        setDate((current) => current ?? result.days[0]?.date ?? null);
      })
      .catch((err) => !cancelled && setCalendarError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!date || phase === "held") return;
    const controller = new AbortController();
    const fetchDay = () =>
      // After the customer's own hold or release (dayVersion > 0) the map must not come from the edge's 2-second cache.
      api<DayAvailability>("/reservations/availability", {
        query: { date, fresh: dayVersion || undefined },
        signal: controller.signal,
      })
        .then((result) => {
          setDay(result);
          setDayError(null);
        })
        .catch((err) => {
          if (!(err instanceof DOMException && err.name === "AbortError")) setDayError(errorMessage(err));
        });
    fetchDay();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") fetchDay();
    }, REFRESH_MS);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [date, phase, dayVersion]);

  // A signed-in customer who already holds karts (for example after a reload) can continue to payment.
  useEffect(() => {
    if (customer.status !== "signed-in") return;
    let cancelled = false;
    api<Reservation[]>("/account/reservations")
      .then((items) => {
        if (cancelled) return;
        const open = items.find((r) => r.status === "held" && r.hold_expires_at && new Date(r.hold_expires_at).getTime() > Date.now());
        setPendingHold(open ?? null);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [customer.status]);

  const session = useMemo(() => day?.sessions.find((s) => s.time === time) ?? null, [day, time]);
  const maxKarts = calendar?.max_karts_per_reservation ?? 7;
  // The seat map refreshes while the customer decides: never ask for more than is still free.
  const singles = session ? Math.min(singlesWanted, session.singles_left) : 0;
  const doubles = session ? Math.min(doublesWanted, session.doubles_left) : 0;
  const singleMax = session ? Math.min(session.singles_left, maxKarts - doubles) : 0;
  const doubleMax = session ? Math.min(session.doubles_left, maxKarts - singles) : 0;
  const total = day ? singles * day.single_price_toman + doubles * day.double_price_toman : 0;
  // With online payment off the seat map still shows what is free; the customer then books by phone.
  const bookingOpen = calendar ? calendar.online_booking_enabled : false;
  const canPay = calendar ? calendar.payments_enabled : false;

  // ---- actions -------------------------------------------------------------------------------------------------------
  function chooseDate(next: string) {
    setDate(next);
    setDay(null);
    setTime(null);
    setSingles(0);
    setDoubles(0);
    setError(null);
  }

  function chooseTime(next: string) {
    setTime(next);
    setError(null);
    const chosen = day?.sessions.find((s) => s.time === next);
    if (chosen && singlesWanted === 0 && doublesWanted === 0 && chosen.singles_left > 0) setSingles(1);
  }

  async function hold(me: Me) {
    if (!date || !time || singles + doubles === 0) return;
    setBusy("hold");
    setError(null);
    try {
      const held = await api<Reservation>("/reservations", {
        method: "POST",
        csrf: me.csrf_token,
        body: { date, time, single_count: singles, double_count: doubles, contact_name: contactName.trim() },
      });
      setReservation(held);
      setPhase("held");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      if (err instanceof ApiError && err.isUnauthenticated) {
        setPhase("login");
      } else {
        setError(errorMessage(err));
        reloadDay();
      }
    } finally {
      setBusy(null);
    }
  }

  function onContinue() {
    if (customer.status === "signed-in") void hold(customer.me);
    else setPhase("login");
  }

  function onSignedIn(me: Me) {
    signedIn(me);
    void hold(me);
  }

  async function pay(target: Reservation) {
    if (customer.status !== "signed-in") {
      setPhase("login");
      return;
    }
    setBusy("pay");
    setError(null);
    try {
      const start = await api<StartPayment>(`/reservations/${target.id}/pay`, { method: "POST", csrf: customer.me.csrf_token });
      goToGateway(start);
      // The browser is leaving for the bank; keep the button busy until it does.
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "انتقال به درگاه بانک ممکن نشد. دوباره تلاش کنید.");
      setBusy(null);
    }
  }

  async function release(target: Reservation) {
    if (customer.status !== "signed-in") return;
    setBusy("release");
    setError(null);
    try {
      await api<void>(`/reservations/${target.id}`, { method: "DELETE", csrf: customer.me.csrf_token });
      restart();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  function restart() {
    setReservation(null);
    setPendingHold(null);
    setPhase("choose");
    setTime(null);
    setSingles(0);
    setDoubles(0);
    reloadDay();
  }

  // ---- render --------------------------------------------------------------------------------------------------------
  if (calendarError) {
    return <Alert tone="error">{calendarError}</Alert>;
  }
  if (!calendar) {
    return (
      <div className="grid min-h-[40vh] place-items-center">
        <Spinner label="در حال بارگذاری سانس‌ها" className="h-9 w-9" />
      </div>
    );
  }

  if (phase === "held" && reservation) {
    return (
      <HoldTicket
        reservation={reservation}
        holdMinutes={calendar.hold_minutes}
        paying={busy === "pay"}
        releasing={busy === "release"}
        error={error}
        onPay={() => pay(reservation)}
        onRelease={() => release(reservation)}
        onRestart={restart}
      />
    );
  }

  if (!bookingOpen || calendar.days.length === 0) {
    return <BookingClosed calendar={calendar} />;
  }

  return (
    <div className="grid gap-8 lg:grid-cols-12 lg:gap-10">
      <div className="space-y-8 lg:col-span-8">
        {pendingHold && (
          <Alert tone="warning" className="flex flex-wrap items-center justify-between gap-3">
            <span>
              رزرو {pendingHold.code} ({fa(pendingHold.time)} {pendingHold.weekday}) هنوز پرداخت نشده و خودروهایش برای شما نگه داشته شده است.
            </span>
            <button
              type="button"
              className={buttonClasses("dark", "sm")}
              onClick={() => {
                setReservation(pendingHold);
                setPhase("held");
              }}
            >
              ادامه پرداخت
            </button>
          </Alert>
        )}

        <div>
          <h2 className="mb-4 flex items-center gap-3 text-lg font-black">
            <StepNumber n={1} /> روز را انتخاب کنید
          </h2>
          <DayStrip days={calendar.days} selected={date} onSelect={chooseDate} />
        </div>

        <div>
          <h2 className="mb-2 flex items-center gap-3 text-lg font-black">
            <StepNumber n={2} /> سانس را انتخاب کنید
          </h2>
          <p className="mb-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-fg-muted">
            <span className="flex items-center gap-2">
              <span className="seat-dot" aria-hidden="true" /> تک‌نفره خالی
            </span>
            <span className="flex items-center gap-2">
              <span className="seat-dot is-double" aria-hidden="true" /> دونفره خالی
            </span>
            <span className="flex items-center gap-2">
              <span className="seat-dot is-taken" aria-hidden="true" /> پر شده
            </span>
            <span className="text-fg-subtle">جای خالی‌ها هر چند ثانیه به‌روز می‌شود.</span>
          </p>
          {day && JUNIOR_DAYS.has(day.weekday) && (
            <p className="mb-5 rounded-2xl bg-surface-2 px-4 py-3 text-sm text-fg-muted">
              نوجوانان ۱۱ تا ۱۴ ساله (با قد بیشتر از ۱۴۰ سانتی‌متر) فقط در سانس‌های ساعت ۱۵ تا ۱۸ همین روز می‌توانند تک‌نفره برانند.
            </p>
          )}
          {dayError && <Alert tone="error">{dayError}</Alert>}
          {!day && !dayError && (
            <div className="grid min-h-40 place-items-center">
              <Spinner label="در حال بارگذاری سانس‌ها" className="h-8 w-8" />
            </div>
          )}
          {day && day.is_closed && <Alert tone="info">این روز رزرو آنلاین ندارد.</Alert>}
          {day && !day.is_closed && <SessionGrid sessions={day.sessions} selected={time} onSelect={chooseTime} />}
        </div>
      </div>

      <aside className="lg:col-span-4">
        <div
          id="booking-summary"
          className="carbon sticky top-24 scroll-mt-24 overflow-hidden rounded-[2rem] p-6 shadow-[0_40px_80px_-40px_rgb(12_13_16/0.9)] md:p-7"
        >
          {phase === "login" && customer.status !== "signed-in" ? (
            <>
              <OtpLogin tone="dark" title="برای نگه داشتن خودروها وارد شوید" onSignedIn={onSignedIn} />
              <button
                type="button"
                onClick={() => setPhase("choose")}
                className="mt-5 text-sm font-bold text-on-carbon-muted underline underline-offset-4 hover:text-on-carbon"
              >
                بازگشت به انتخاب سانس
              </button>
            </>
          ) : (
            <Summary
              day={day}
              time={time}
              singles={singles}
              doubles={doubles}
              singleMax={singleMax}
              doubleMax={doubleMax}
              total={total}
              holdMinutes={calendar.hold_minutes}
              contactName={contactName}
              onContactName={setContactName}
              onSingles={setSingles}
              onDoubles={setDoubles}
              onContinue={onContinue}
              busy={busy === "hold" || customer.status === "loading"}
              error={error}
              canPay={canPay}
            />
          )}
        </div>
      </aside>
      {phase === "choose" && day && time && (
        <MobileBar time={time} karts={karts(singles, doubles)} total={total} />
      )}
    </div>
  );
}

/** Phones: the summary is below 40 session tiles, so a bottom bar shows the choice and jumps to it (like cinema apps). */
function MobileBar({ time, karts: chosen, total }: { time: string; karts: string; total: number }) {
  useEffect(() => {
    document.body.dataset.stickyBar = "1"; // lifts the chat launcher above the bar (globals.css)
    return () => {
      delete document.body.dataset.stickyBar;
    };
  }, []);
  return (
    <div className="carbon fixed inset-x-0 bottom-0 z-30 border-t border-carbon-line px-4 pb-[max(env(safe-area-inset-bottom),0.75rem)] pt-3 shadow-[0_-20px_40px_-20px_rgb(0_0_0/0.6)] lg:hidden">
      <div className="mx-auto flex max-w-xl items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate text-sm font-black">
            ساعت {fa(time)} · {chosen}
          </p>
          <p className="text-sm font-bold text-accent">{toman(total)}</p>
        </div>
        <button
          type="button"
          onClick={() => document.getElementById("booking-summary")?.scrollIntoView({ behavior: "smooth", block: "start" })}
          className={buttonClasses("primary", "md", "shrink-0")}
        >
          ادامه
        </button>
      </div>
    </div>
  );
}

function StepNumber({ n }: { n: number }) {
  return <span className="grid h-8 w-8 place-items-center rounded-full bg-ink text-sm font-black text-accent">{fa(n)}</span>;
}

type SummaryProps = {
  day: DayAvailability | null;
  time: string | null;
  singles: number;
  doubles: number;
  singleMax: number;
  doubleMax: number;
  total: number;
  holdMinutes: number;
  contactName: string;
  onContactName: (value: string) => void;
  onSingles: (value: number) => void;
  onDoubles: (value: number) => void;
  onContinue: () => void;
  busy: boolean;
  error: string | null;
  canPay: boolean;
};

function Summary(props: SummaryProps) {
  const { day, time, singles, doubles, total } = props;
  if (!day || !time) {
    return (
      <div className="py-6 text-center">
        <p className="text-xl font-black">سانس دلخواه را انتخاب کنید</p>
        <p className="mt-3 text-on-carbon-muted">روی یکی از ساعت‌های خالی بزنید تا تعداد خودرو و مبلغ را ببینید.</p>
      </div>
    );
  }
  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-bold text-accent">انتخاب شما</p>
        <p className="mt-2 text-2xl font-black">
          {day.weekday} {jalali(day.date_jalali)}، ساعت {fa(time)}
        </p>
        {day.is_holiday && <p className="mt-1 text-xs text-on-carbon-muted">قیمت روز تعطیل</p>}
      </div>

      <KartStepper
        label="تک‌نفره"
        hint="از ۱۶ سال؛ ۱۱ تا ۱۴ سال با شرط"
        price={day.single_price_toman}
        value={singles}
        max={props.singleMax}
        onChange={props.onSingles}
      />
      <KartStepper
        label="دونفره"
        hint="راننده ۱۸+ با گواهینامه، عقب کودک ۴ تا ۱۵"
        price={day.double_price_toman}
        value={doubles}
        max={props.doubleMax}
        onChange={props.onDoubles}
      />

      <div>
        <label htmlFor="contact-name" className="label text-on-carbon-muted">
          نام روی بلیت (اختیاری)
        </label>
        <input
          id="contact-name"
          className="field field-dark"
          value={props.contactName}
          onChange={(event) => props.onContactName(event.target.value)}
          maxLength={80}
          autoComplete="name"
        />
      </div>

      <div className="flex items-end justify-between border-t border-carbon-line pt-5">
        <span className="text-on-carbon-muted">{karts(singles, doubles)}</span>
        <span className="text-right">
          <span className="block text-xs text-on-carbon-muted">جمع کل</span>
          <span className="text-2xl font-black text-accent">{toman(total)}</span>
        </span>
      </div>

      {props.error && <Alert tone="error">{props.error}</Alert>}

      {props.canPay ? (
        <>
          <button
            type="button"
            onClick={props.onContinue}
            disabled={props.busy || singles + doubles === 0}
            className={buttonClasses("primary", "lg", "w-full")}
          >
            {props.busy ? <Spinner label="در حال نگه داشتن خودروها" /> : "ادامه و پرداخت"}
          </button>
          <p className="text-center text-xs leading-6 text-on-carbon-muted">
            خودروها {fa(props.holdMinutes)} دقیقه برای پرداخت نگه داشته می‌شوند. مبلغ نهایی را سرور حساب می‌کند.
          </p>
        </>
      ) : (
        <>
          <a href={site.contact.phone.href} className={buttonClasses("primary", "lg", "w-full")}>
            <PhoneIcon className="h-5 w-5" />
            تماس برای رزرو این سانس
          </a>
          <p className="text-center text-xs leading-6 text-on-carbon-muted">
            پرداخت آنلاین به‌زودی فعال می‌شود؛ فعلاً سانس را تلفنی رزرو کنید. جای خالی‌ها همین حالا به‌روز است.
          </p>
        </>
      )}
    </div>
  );
}

function BookingClosed({ calendar }: { calendar: BookingCalendar }) {
  const reason = !calendar.online_booking_enabled
    ? "رزرو آنلاین فعلاً بسته است."
    : "در حال حاضر روزی برای رزرو آنلاین باز نیست.";
  return (
    <div className="carbon mx-auto max-w-2xl rounded-[2rem] p-8 text-center md:p-12">
      <p className="text-2xl font-black">{reason}</p>
      <p className="mt-4 text-on-carbon-muted">تا آن موقع می‌توانید تلفنی رزرو کنید؛ همکاران ما سانس خالی را برایتان پیدا می‌کنند.</p>
      <a href={site.contact.phone.href} className={buttonClasses("primary", "lg", "mt-8")}>
        <PhoneIcon className="h-5 w-5" />
        تماس برای رزرو
      </a>
      <p className="mt-6 text-sm text-on-carbon-muted">
        <Link href={hrefFor("/faq", SPLIT_HOSTS)} className="underline underline-offset-4">
          سوالات متداول
        </Link>
      </p>
    </div>
  );
}
