"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { OtpLogin } from "@/components/auth/otp-login";
import { useCountdown } from "@/components/booking/use-countdown";
import { CrewStep } from "@/components/booking/wizard/crew-step";
import { DayStep } from "@/components/booking/wizard/day-step";
import { EMPTY_CREW, planKarts, type Crew } from "@/components/booking/wizard/crew";
import { LapTracker, seconds, sectorTone, type Sector } from "@/components/booking/wizard/lap-tracker";
import { LaunchButton } from "@/components/booking/wizard/launch-button";
import { RacePass } from "@/components/booking/wizard/race-pass";
import { SessionStep } from "@/components/booking/wizard/session-step";
import { TeamRadio } from "@/components/booking/wizard/team-radio";
import { buttonClasses } from "@/components/button-link";
import { ArrowLeftIcon, PhoneIcon, ShieldIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { site } from "@/content/site";
import { ApiError, api, errorMessage } from "@/lib/api";
import { fa, jalali, karts, toman } from "@/lib/format";
import { goToGateway } from "@/lib/gateway";
import { SPLIT_HOSTS, hrefFor } from "@/lib/urls";
import type { BookingCalendar, BookingInfo, DayAvailability, Me, Reservation, StartPayment } from "@/lib/types";
import { useCustomer } from "@/lib/use-customer";

const REFRESH_MS = 20_000; // seat counts are refreshed while the customer is choosing
const STEPS = ["crew", "day", "session", "finish"] as const;
type Step = (typeof STEPS)[number];

const TITLES: Record<Step, { title: string; sector: string }> = {
  crew: { title: "چه کسانی پشت فرمان می‌نشینند؟", sector: "خدمه" },
  day: { title: "کدام روز به پیست می‌آیید؟", sector: "روز" },
  session: { title: "سانس را از روی جدول استارت انتخاب کنید", sector: "سانس" },
  finish: { title: "پاس شما آماده است", sector: "پایان" },
};

/**
 * Online booking as one lap of the Davos circuit: crew → day → session → launch. A kart drives round the real track as
 * the customer moves on, each step is timed like a sector, and the booking is sent with a press-and-hold "launch
 * control". The API rules are unchanged: the server holds the karts, prices them, and the bank takes the payment.
 */
export function BookingWizard() {
  const { state: customer, signedIn } = useCustomer();
  const [calendar, setCalendar] = useState<BookingCalendar | null>(null);
  const [calendarError, setCalendarError] = useState<string | null>(null);
  const [info, setInfo] = useState<BookingInfo | null>(null);
  const [step, setStep] = useState<Step>("crew");
  const [crew, setCrew] = useState<Crew>(EMPTY_CREW);
  const [teensDrive, setTeensDrive] = useState(true);
  const [manual, setManual] = useState(false);
  const [manualSingles, setManualSingles] = useState(1);
  const [manualDoubles, setManualDoubles] = useState(0);
  const [date, setDate] = useState<string | null>(null);
  const [day, setDay] = useState<DayAvailability | null>(null);
  const [dayError, setDayError] = useState<string | null>(null);
  const [dayVersion, setDayVersion] = useState(0);
  const [time, setTime] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [pendingHold, setPendingHold] = useState<Reservation | null>(null);
  const [busy, setBusy] = useState<"hold" | "pay" | "release" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [launchAttempt, setLaunchAttempt] = useState(0);
  const [sectors, setSectors] = useState<Record<Step, number | null>>({ crew: null, day: null, session: null, finish: null });
  const enteredAt = useRef<number>(0);
  const headingRef = useRef<HTMLHeadingElement>(null);

  const maxKarts = calendar?.max_karts_per_reservation ?? 7;
  const plan = useMemo(() => {
    if (!manual) return planKarts(crew, teensDrive, maxKarts);
    const total = manualSingles + manualDoubles;
    const base = { singles: manualSingles, doubles: manualDoubles, teenDrivers: 0, people: manualSingles + manualDoubles * 2 };
    if (total === 0) return { ok: false as const, reason: "حداقل یک خودرو انتخاب کنید.", ...base };
    if (total > maxKarts) return { ok: false as const, reason: `در هر رزرو حداکثر ${fa(maxKarts)} خودرو.`, ...base };
    return { ok: true as const, ...base };
  }, [manual, crew, teensDrive, maxKarts, manualSingles, manualDoubles]);

  // ---- data ----------------------------------------------------------------------------------------------------------
  useEffect(() => {
    enteredAt.current = performance.now();
    let cancelled = false;
    api<BookingCalendar>("/reservations/calendar")
      .then((result) => !cancelled && setCalendar(result))
      .catch((err) => !cancelled && setCalendarError(errorMessage(err)));
    // The daily cutoff (online booking closes at a fixed hour, every day) is only in the settings summary.
    api<BookingInfo>("/reservations/info")
      .then((result) => !cancelled && setInfo(result))
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!date || reservation) return;
    const controller = new AbortController();
    const fetchDay = () =>
      api<DayAvailability>("/reservations/availability", { query: { date, fresh: dayVersion || undefined }, signal: controller.signal })
        .then((result) => {
          setDay(result);
          setDayError(null);
        })
        .catch((err) => {
          if (!(err instanceof DOMException && err.name === "AbortError")) setDayError(errorMessage(err));
        });
    fetchDay();
    const timer = window.setInterval(() => document.visibilityState === "visible" && fetchDay(), REFRESH_MS);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [date, reservation, dayVersion]);

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

  // ---- navigation ----------------------------------------------------------------------------------------------------
  function go(next: Step) {
    const now = performance.now();
    const leaving = step;
    // A sector is timed the first time it is completed (going back does not reset the clock of finished sectors).
    // Read the clock now: the state updater runs later, after enteredAt has moved on.
    const elapsed = now - enteredAt.current;
    if (STEPS.indexOf(next) > STEPS.indexOf(leaving)) {
      setSectors((s) => (s[leaving] === null ? { ...s, [leaving]: elapsed } : s));
    }
    enteredAt.current = now;
    setError(null);
    setStep(next);
    requestAnimationFrame(() => {
      headingRef.current?.focus({ preventScroll: true });
      document.getElementById("wizard-top")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  function chooseDate(next: string) {
    if (next !== date) {
      setDate(next);
      setDay(null);
      setTime(null);
    }
    window.setTimeout(() => go("session"), 260);
  }

  function chooseTime(next: string) {
    setTime(next);
    window.setTimeout(() => go("finish"), 300);
  }

  // ---- booking actions (unchanged API flow) --------------------------------------------------------------------------
  async function hold(me: Me) {
    if (!date || !time || !plan.ok) return;
    setBusy("hold");
    setError(null);
    try {
      const held = await api<Reservation>("/reservations", {
        method: "POST",
        csrf: me.csrf_token,
        body: { date, time, single_count: plan.singles, double_count: plan.doubles, contact_name: name.trim() },
      });
      const finishMs = performance.now() - enteredAt.current;
      setSectors((s) => ({ ...s, finish: finishMs }));
      setReservation(held);
      document.getElementById("wizard-top")?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      setError(err instanceof ApiError && err.isUnauthenticated ? "نشست شما تمام شده؛ دوباره وارد شوید." : errorMessage(err));
      setDayVersion((v) => v + 1);
      setLaunchAttempt((n) => n + 1); // re-arms the launch button
      if ("vibrate" in navigator) navigator.vibrate?.([80, 60, 80]);
    } finally {
      setBusy(null);
    }
  }

  async function pay(target: Reservation) {
    if (customer.status !== "signed-in") return;
    setBusy("pay");
    setError(null);
    try {
      const start = await api<StartPayment>(`/reservations/${target.id}/pay`, { method: "POST", csrf: customer.me.csrf_token });
      goToGateway(start);
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
      setReservation(null);
      setPendingHold(null);
      setTime(null);
      setDayVersion((v) => v + 1);
      setSectors({ crew: null, day: null, session: null, finish: null });
      enteredAt.current = performance.now();
      setStep("session");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  /** An expired hold is already gone on the server: start the session choice again without calling the API. */
  function restart() {
    setReservation(null);
    setPendingHold(null);
    setTime(null);
    setDayVersion((v) => v + 1);
    setSectors({ crew: null, day: null, session: null, finish: null });
    enteredAt.current = performance.now();
    setStep("session");
  }

  // ---- render --------------------------------------------------------------------------------------------------------
  if (calendarError) return <Alert tone="error">{calendarError}</Alert>;
  if (!calendar) {
    return (
      <div className="grid min-h-[50vh] place-items-center">
        <Spinner label="در حال روشن کردن موتورها" className="h-9 w-9" />
      </div>
    );
  }
  if (!calendar.online_booking_enabled || calendar.days.length === 0) return <BookingClosed calendar={calendar} />;

  const selectedDay = calendar.days.find((d) => d.date === date) ?? null;
  const dayLabel = selectedDay ? `${selectedDay.weekday} ${jalali(selectedDay.date_jalali)}` : "";
  const total = selectedDay ? plan.singles * selectedDay.single_price_toman + plan.doubles * selectedDay.double_price_toman : 0;
  const stepIndex = STEPS.indexOf(step);
  const progress = reservation ? 1 : stepIndex / STEPS.length;
  const sectorList: Sector[] = STEPS.map((key) => ({ key, label: TITLES[key].sector, ms: sectors[key] }));
  const lapMs = STEPS.reduce((sum, key) => sum + (sectors[key] ?? 0), 0);

  const radio = reservation
    ? `باکس، باکس! خودروها مال شماست. ${fa(calendar.hold_minutes)} دقیقه برای پرداخت وقت داری.`
    : step === "crew"
      ? "سلام راننده! بگو کی‌ها میان پیست؛ خودروها رو خودم برات می‌چینم."
      : step === "day"
        ? plan.ok
          ? `گاراژ آماده‌ست: ${karts(plan.singles, plan.doubles)}. حالا کدوم روز؟`
          : "اول ترکیب گروه رو درست کن."
        : step === "session"
          ? "خونه‌های زرد روی جدول استارت، جای خودروهای شماست. یه سانس انتخاب کن."
          : customer.status === "signed-in"
            ? "همه‌چی آماده‌ست. دکمه رو نگه دار تا چراغ‌ها خاموش شن!"
            : "یه قدم مونده: با شماره موبایلت وارد شو.";

  return (
    <div id="wizard-top" className="scroll-mt-20">
      {pendingHold && !reservation && (
        <Alert tone="warning" className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <span>
            رزرو {pendingHold.code} ({fa(pendingHold.time)} {pendingHold.weekday}) هنوز پرداخت نشده و خودروهایش برای شما نگه داشته شده است.
          </span>
          <button type="button" className={buttonClasses("primary", "sm")} onClick={() => setReservation(pendingHold)}>
            ادامه پرداخت
          </button>
        </Alert>
      )}

      {info?.online_booking_cutoff_passed && !reservation && <CutoffNotice cutoff={info.online_booking_cutoff} />}

      <div className="grid gap-6 lg:grid-cols-12 lg:gap-10">
        <div className="min-w-0 lg:col-span-7">
          {/* Phones: the lap and the sector times stay in view above the step. */}
          <div className="sticky top-[4.5rem] z-20 -mx-1 mb-5 rounded-2xl border border-white/10 bg-[#0c0d10]/95 p-3 shadow-[0_14px_30px_-16px_rgb(0_0_0/0.9)] backdrop-blur-xl lg:hidden">
            <LapTracker progress={progress} sectors={sectorList} compact />
          </div>

          {reservation ? (
            <HeldView
              reservation={reservation}
              holdMinutes={calendar.hold_minutes}
              lapMs={lapMs}
              sectors={sectorList}
              name={name}
              paying={busy === "pay"}
              releasing={busy === "release"}
              error={error}
              onPay={() => pay(reservation)}
              onRelease={() => release(reservation)}
              onRestart={restart}
              radio={radio}
            />
          ) : (
            <section aria-labelledby="wizard-step-title" key={step} className="wizard-step">
              <div className="flex items-center justify-between gap-3">
                <p className="race-number text-xs font-bold tracking-[0.25em] text-fg-subtle" dir="ltr">
                  {stepIndex < 3 ? `SECTOR ${stepIndex + 1}` : "FINAL"} · {stepIndex + 1}/{STEPS.length}
                </p>
                {stepIndex > 0 && (
                  <button
                    type="button"
                    onClick={() => go(STEPS[stepIndex - 1])}
                    className="flex items-center gap-1.5 rounded-full border border-white/12 px-3 py-1.5 text-sm font-bold text-fg-muted transition hover:border-white/30 hover:text-fg"
                  >
                    <ArrowLeftIcon className="h-4 w-4 rotate-180" />
                    مرحله قبل
                  </button>
                )}
              </div>
              <h2 id="wizard-step-title" ref={headingRef} tabIndex={-1} className="mt-3 text-[clamp(1.6rem,5vw,2.4rem)] font-black leading-tight outline-none">
                {TITLES[step].title}
              </h2>
              <div className="mt-4">
                <TeamRadio message={radio} />
              </div>

              <div className="mt-6">
                {step === "crew" && (
                  <CrewStep
                    crew={crew}
                    onCrew={setCrew}
                    teensDrive={teensDrive}
                    onTeensDrive={setTeensDrive}
                    plan={plan}
                    manual={manual}
                    onManual={setManual}
                    manualSingles={manualSingles}
                    manualDoubles={manualDoubles}
                    onManualSingles={(v) => setManualSingles(Math.max(0, v))}
                    onManualDoubles={(v) => setManualDoubles(Math.max(0, v))}
                    maxKarts={maxKarts}
                  />
                )}
                {step === "day" && (
                  <DayStep
                    days={calendar.days}
                    selected={date}
                    onSelect={chooseDate}
                    singles={plan.singles}
                    doubles={plan.doubles}
                    teenDrivers={plan.teenDrivers}
                  />
                )}
                {step === "session" && (
                  <>
                    {dayError && <Alert tone="error">{dayError}</Alert>}
                    {!day && !dayError && (
                      <div className="grid min-h-48 place-items-center">
                        <Spinner label="در حال خواندن جدول استارت" className="h-8 w-8" />
                      </div>
                    )}
                    {day && day.is_closed && <Alert tone="info">این روز رزرو آنلاین ندارد؛ روز دیگری را انتخاب کنید.</Alert>}
                    {day && !day.is_closed && (
                      <SessionStep
                        cutoffPassed={info?.online_booking_cutoff_passed ?? false}
                        sessions={day.sessions}
                        selected={time}
                        onSelect={chooseTime}
                        singles={plan.singles}
                        doubles={plan.doubles}
                        teenDrivers={plan.teenDrivers}
                      />
                    )}
                  </>
                )}
                {step === "finish" && (
                  <FinishStep
                    canPay={calendar.payments_enabled}
                    signedInMe={customer.status === "signed-in" ? customer.me : null}
                    loading={customer.status === "loading"}
                    onSignedIn={signedIn}
                    name={name}
                    onName={setName}
                    onLaunch={(me) => hold(me)}
                    busy={busy === "hold"}
                    error={error}
                    holdMinutes={calendar.hold_minutes}
                    launchAttempt={launchAttempt}
                    pass={
                      <div className="lg:hidden">
                        <RacePass dayLabel={dayLabel} time={time} singles={plan.singles} doubles={plan.doubles} total={total} name={name} />
                      </div>
                    }
                  />
                )}
              </div>

              {step === "crew" && (
                <StepBar
                  summary={plan.ok ? karts(plan.singles, plan.doubles) : "ترکیب گروه را کامل کنید"}
                  detail={plan.ok ? `${fa(plan.people)} نفر` : ""}
                  action="انتخاب روز"
                  disabled={!plan.ok}
                  onNext={() => go("day")}
                />
              )}
              {step === "day" && date && (
                <StepBar summary={dayLabel} detail={toman(total)} action="سانس‌های این روز" onNext={() => go("session")} />
              )}
              {step === "session" && time && (
                <StepBar summary={`${dayLabel}، ساعت ${fa(time)}`} detail={toman(total)} action="ادامه" onNext={() => go("finish")} />
              )}
            </section>
          )}
        </div>

        {/* Computers: the pit board beside the steps, with the lap and the pass filling in live. */}
        <aside className="hidden lg:col-span-5 lg:block">
          <div className="sticky top-28 space-y-5">
            <div className="carbon rounded-[1.75rem] border border-white/10 p-5">
              <p className="mb-3 flex items-center justify-between text-sm font-black">
                <span>دور رزرو شما</span>
                {lapMs > 0 && (
                  <span className="race-number text-xs" style={{ color: sectorTone(lapMs / 4) }} dir="ltr">
                    {seconds(lapMs)}s
                  </span>
                )}
              </p>
              <LapTracker progress={progress} sectors={sectorList} />
            </div>
            {!reservation && (
              <RacePass dayLabel={dayLabel} time={time} singles={plan.ok ? plan.singles : 0} doubles={plan.ok ? plan.doubles : 0} total={total} name={name} />
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

/** Shown once the day's online-booking hour has passed: the plan can still be made, and the phone is one tap away. */
function CutoffNotice({ cutoff }: { cutoff: string | null }) {
  return (
    <div className="mb-6 flex flex-col gap-4 rounded-[1.6rem] border border-signal/35 bg-signal/[0.08] p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
      <div className="flex items-start gap-3">
        <span className="start-lamp lamp-static mt-1 shrink-0" aria-hidden="true" />
        <div>
          <p className="font-black">پیت‌لین آنلاین امروز بسته شد</p>
          <p className="mt-1 text-sm leading-7 text-fg-muted">
            رزرو آنلاین هر روز تا ساعت {cutoff ? fa(cutoff) : "۱۵"} باز است و از نیمه‌شب دوباره باز می‌شود. برنامه را همین حالا بچینید و
            از نیمه‌شب ثبت کنید، یا تماس بگیرید.
          </p>
        </div>
      </div>
      <a href={site.contact.phone.href} className={buttonClasses("primary", "md", "shrink-0")}>
        <PhoneIcon className="h-5 w-5" />
        تماس برای رزرو
      </a>
    </div>
  );
}

/** The step's bottom bar: what is chosen so far and the button onwards. Sticks to the bottom of the screen on phones. */
function StepBar({ summary, detail, action, onNext, disabled }: { summary: string; detail: string; action: string; onNext: () => void; disabled?: boolean }) {
  useEffect(() => {
    document.body.dataset.stickyBar = "1"; // lifts the chat launcher above the bar (globals.css)
    return () => {
      delete document.body.dataset.stickyBar;
    };
  }, []);
  return (
    <div className="glass sticky bottom-3 z-20 mt-8 flex items-center justify-between gap-3 rounded-[1.4rem] p-2.5 ps-4 shadow-[0_20px_40px_-20px_rgb(0_0_0/0.9)]">
      <div className="min-w-0">
        <p className="truncate text-sm font-black">{summary}</p>
        {detail && <p className="truncate text-xs font-bold text-accent">{detail}</p>}
      </div>
      <button type="button" onClick={onNext} disabled={disabled} className={buttonClasses("primary", "md", "shrink-0")}>
        {action}
      </button>
    </div>
  );
}

type FinishStepProps = {
  canPay: boolean;
  signedInMe: Me | null;
  loading: boolean;
  onSignedIn: (me: Me) => void;
  name: string;
  onName: (value: string) => void;
  onLaunch: (me: Me) => void;
  busy: boolean;
  error: string | null;
  holdMinutes: number;
  launchAttempt: number;
  pass: ReactNode;
};

function FinishStep(props: FinishStepProps) {
  if (!props.canPay) {
    return (
      <div className="space-y-5">
        {props.pass}
        <a href={site.contact.phone.href} className={buttonClasses("primary", "lg", "w-full")}>
          <PhoneIcon className="h-5 w-5" />
          تماس برای رزرو این سانس
        </a>
        <p className="text-center text-sm text-fg-muted">پرداخت آنلاین به‌زودی فعال می‌شود؛ فعلاً سانس را تلفنی رزرو کنید.</p>
      </div>
    );
  }
  return (
    <div className="space-y-5">
      {props.pass}
      <div>
        <label htmlFor="pass-name" className="label text-fg-muted">
          نام روی پاس (اختیاری)
        </label>
        <input
          id="pass-name"
          className="field"
          value={props.name}
          onChange={(event) => props.onName(event.target.value)}
          maxLength={80}
          autoComplete="name"
          placeholder="مثلاً علی رضایی"
        />
      </div>
      {props.error && <Alert tone="error">{props.error}</Alert>}
      {props.signedInMe ? (
        <>
          <LaunchButton key={props.launchAttempt} onLaunch={() => props.onLaunch(props.signedInMe!)} busy={props.busy} />
          <p className="text-center text-xs leading-6 text-fg-muted">
            خودروها {fa(props.holdMinutes)} دقیقه برای پرداخت نگه داشته می‌شوند. مبلغ نهایی را سرور حساب می‌کند.
          </p>
        </>
      ) : props.loading ? (
        <div className="grid min-h-24 place-items-center">
          <Spinner label="در حال بررسی ورود" className="h-7 w-7" />
        </div>
      ) : (
        <div className="carbon rounded-[1.6rem] border border-white/10 p-5">
          <OtpLogin tone="dark" title="برای ثبت، با موبایل وارد شوید" onSignedIn={props.onSignedIn} />
        </div>
      )}
    </div>
  );
}

function HeldView(props: {
  reservation: Reservation;
  holdMinutes: number;
  lapMs: number;
  sectors: Sector[];
  name: string;
  paying: boolean;
  releasing: boolean;
  error: string | null;
  onPay: () => void;
  onRelease: () => void;
  onRestart: () => void;
  radio: string;
}) {
  const { reservation } = props;
  const left = useCountdown(reservation.hold_expires_at);
  const expired = left !== null && left <= 0;
  const totalSeconds = Math.max(1, props.holdMinutes * 60);
  const progress = left === null ? 1 : Math.min(1, left / totalSeconds);
  const mm = left === null ? "" : `${fa(Math.floor(left / 60))}:${fa(String(left % 60).padStart(2, "0"))}`;
  return (
    <section aria-labelledby="held-title" className="wizard-step space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="race-number text-xs font-bold tracking-[0.25em] text-go" dir="ltr">
            CHEQUERED FLAG
          </p>
          <h2 id="held-title" className="mt-2 text-[clamp(1.6rem,5vw,2.4rem)] font-black leading-tight">
            خودروها برای شما نگه داشته شد
          </h2>
        </div>
        {props.lapMs > 0 && (
          <div className="glass rounded-2xl px-4 py-2 text-center">
            <p className="text-[0.7rem] font-bold text-fg-muted">زمان دور رزرو شما</p>
            <p className="race-number text-2xl font-black" style={{ color: sectorTone(props.lapMs / 4) }} dir="ltr">
              {seconds(props.lapMs)}s
            </p>
          </div>
        )}
      </div>
      <TeamRadio message={props.radio} />
      <RacePass
        dayLabel={`${reservation.weekday} ${jalali(reservation.date_jalali)}`}
        time={reservation.time}
        singles={reservation.single_count}
        doubles={reservation.double_count}
        total={reservation.amount_toman}
        name={reservation.contact_name || props.name}
        code={reservation.code}
        footer={
          <div className="flex items-center gap-4">
            <div
              className="grid h-16 w-16 shrink-0 place-items-center rounded-full"
              style={{ background: `conic-gradient(${expired ? "#d90a00" : "#ffc400"} ${progress * 360}deg, rgb(255 255 255 / 0.1) 0)` }}
              role="timer"
              aria-label={expired ? "زمان نگه‌داری تمام شد" : `زمان باقی‌مانده ${mm}`}
            >
              <span className="grid h-[3.4rem] w-[3.4rem] place-items-center rounded-full bg-[#0b0c0f] text-sm font-black" dir="ltr">
                {expired ? "۰:۰۰" : mm}
              </span>
            </div>
            <p className="text-sm leading-6 text-on-carbon-muted">
              {expired ? "زمان نگه‌داری تمام شد؛ دوباره سانس را انتخاب کنید." : "تا پایان این زمان، خودروها فقط برای شماست."}
            </p>
          </div>
        }
      />
      {props.error && <Alert tone="error">{props.error}</Alert>}
      {expired ? (
        <button type="button" onClick={props.onRestart} className={buttonClasses("primary", "lg", "w-full")}>
          انتخاب دوباره
        </button>
      ) : (
        <>
          <button type="button" onClick={props.onPay} disabled={props.paying || props.releasing} className={buttonClasses("primary", "lg", "w-full")}>
            {props.paying ? <Spinner label="در حال انتقال به بانک" /> : `پرداخت ${toman(reservation.amount_toman)}`}
          </button>
          <p className="flex items-center justify-center gap-2 text-center text-xs text-fg-muted">
            <ShieldIcon className="h-4 w-4 text-go" />
            پرداخت در صفحه رسمی بانک ملت (شاپرک) انجام می‌شود؛ اطلاعات کارت را فقط آنجا وارد کنید.
          </p>
          <button
            type="button"
            onClick={props.onRelease}
            disabled={props.paying || props.releasing}
            className="mx-auto block text-sm font-bold text-fg-muted underline underline-offset-4 hover:text-fg"
          >
            {props.releasing ? "در حال آزاد کردن..." : "انصراف و آزاد کردن خودروها"}
          </button>
        </>
      )}
    </section>
  );
}

function BookingClosed({ calendar }: { calendar: BookingCalendar }) {
  const reason = !calendar.online_booking_enabled ? "رزرو آنلاین فعلاً بسته است." : "در حال حاضر روزی برای رزرو آنلاین باز نیست.";
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
