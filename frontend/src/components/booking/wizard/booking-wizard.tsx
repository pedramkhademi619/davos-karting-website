"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { OtpLogin } from "@/components/auth/otp-login";
import { useCountdown } from "@/components/booking/use-countdown";
import { CrewStep } from "@/components/booking/wizard/crew-step";
import { DayStep } from "@/components/booking/wizard/day-step";
import { DEFAULT_JUNIOR_WINDOW, EMPTY_CREW, juniorRule, planKarts, type Crew, type JuniorWindow } from "@/components/booking/wizard/crew";
import { FixSheet, type Fix } from "@/components/booking/wizard/fix-sheet";
import { LapTracker, type Sector } from "@/components/booking/wizard/lap-tracker";
import { LaunchButton } from "@/components/booking/wizard/launch-button";
import { RacePass } from "@/components/booking/wizard/race-pass";
import { SessionStep } from "@/components/booking/wizard/session-step";
import { TeamRadio } from "@/components/booking/wizard/team-radio";
import { TermsPledge, WeatherNote } from "@/components/booking/wizard/terms-pledge";
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
import { Skeleton } from "@/components/ui/skeleton";
import { JALALI_MONTHS } from "@/lib/jalali";

const REFRESH_MS = 20_000; // seat counts are refreshed while the customer is choosing
const STEPS = ["crew", "day", "session", "finish"] as const;
type Step = (typeof STEPS)[number];

const TITLES: Record<Step, { title: string; sector: string }> = {
  crew: { title: "چند نفرید؟", sector: "نفرات" },
  day: { title: "کدام روز به پیست می‌آیید؟", sector: "روز" },
  session: { title: "چه ساعتی؟", sector: "ساعت" },
  finish: { title: "یک قدم تا قطعی شدن", sector: "پرداخت" },
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
  const [accepted, setAccepted] = useState(false);
  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [pendingHold, setPendingHold] = useState<Reservation | null>(null);
  const [busy, setBusy] = useState<"hold" | "pay" | "release" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [launchAttempt, setLaunchAttempt] = useState(0);
  const [fix, setFix] = useState<Fix | null>(null);
  const [sectors, setSectors] = useState<Record<Step, number | null>>({ crew: null, day: null, session: null, finish: null });
  const enteredAt = useRef<number>(0);
  const headingRef = useRef<HTMLHeadingElement>(null);

  const maxKarts = calendar?.max_karts_per_reservation ?? 7;
  const juniorWindow: JuniorWindow = useMemo(
    () =>
      info
        ? { days: new Set(info.junior_weekdays), from: info.junior_from, until: info.junior_until, everyone: info.junior_scope === "everyone" }
        : DEFAULT_JUNIOR_WINDOW,
    [info],
  );
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
    // The booking settings summary (kart counts, junior hours, prices) is read apart from the calendar.
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
    if (!date || !time || !plan.ok || !accepted) return;
    setBusy("hold");
    setError(null);
    try {
      const held = await api<Reservation>("/reservations", {
        method: "POST",
        csrf: me.csrf_token,
        body: { date, time, single_count: plan.singles, double_count: plan.doubles, contact_name: name.trim(), accepted_terms: true },
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

  /** The fix sheet's way out for teens: seat them behind an adult, keep the day or session that was tapped. */
  function seatTeensAndKeep() {
    const current = fix;
    setTeensDrive(false);
    setFix(null);
    if (current?.reason === "teen-day") chooseDate(current.date);
    if (current?.reason === "teen-time") chooseTime(current.time);
  }

  function editCrew() {
    setFix(null);
    go("crew");
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
      <div role="status" className="space-y-4 py-4">
        <span className="sr-only">در حال روشن کردن موتورها</span>
        <Skeleton className="h-28 rounded-3xl" />
        <Skeleton className="h-16 rounded-3xl" />
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-32 rounded-3xl" />
          <Skeleton className="h-32 rounded-3xl" />
        </div>
        <p aria-hidden="true" className="pt-2 text-center text-sm font-bold text-on-carbon-muted">موتورها دارند گرم می‌شوند…</p>
      </div>
    );
  }
  if (!calendar.online_booking_enabled || calendar.days.length === 0) return <BookingClosed calendar={calendar} />;

  const selectedDay = calendar.days.find((d) => d.date === date) ?? null;
  // The cheapest bookable day for the suggested karts: shown on the first step so nobody has to guess the price.
  const fromPrice = calendar.days.length
    ? Math.min(...calendar.days.map((d) => plan.singles * d.single_price_toman + plan.doubles * d.double_price_toman))
    : 0;
  const dayLabel = selectedDay ? `${selectedDay.weekday} ${jalali(selectedDay.date_jalali)}` : "";
  const total = selectedDay ? plan.singles * selectedDay.single_price_toman + plan.doubles * selectedDay.double_price_toman : 0;
  const stepIndex = STEPS.indexOf(step);
  const progress = reservation ? 1 : stepIndex / STEPS.length;
  // The under-15 hours bind this crew when a teen drives, or, if the owner applies them to everyone, when anyone under 15 comes.
  const juniorBound = plan.teenDrivers > 0 || (juniorWindow.everyone && !manual && crew.kid + crew.teen > 0);
  const juniorWho = juniorWindow.everyone ? "زیر ۱۵ سال‌ها" : "رانندگی نوجوان‌ها";
  // What the crew becomes with the teens in the back seat (offered by the fix sheet; no help when the hours bind everyone).
  const seated = !manual && crew.teen > 0 && !juniorWindow.everyone ? planKarts(crew, false, maxKarts) : null;
  const fixDay = fix?.reason === "teen-day" ? calendar.days.find((d) => d.date === fix.date) ?? null : selectedDay;
  const passengersAlternative = seated
    ? seated.ok
      ? {
          ok: true as const,
          singles: seated.singles,
          doubles: seated.doubles,
          price: fixDay ? seated.singles * fixDay.single_price_toman + seated.doubles * fixDay.double_price_toman : 0,
        }
      : crew.kid + crew.teen > crew.licensed
        ? { ok: false as const, missingDrivers: crew.kid + crew.teen - crew.licensed }
        : null
    : null;
  const sectorList: Sector[] = STEPS.map((key) => ({ key, label: TITLES[key].sector, ms: sectors[key] }));
  const lapMs = STEPS.reduce((sum, key) => sum + (sectors[key] ?? 0), 0);

  const radio = reservation
    ? `خودروها برای شما نگه داشته شد. ${fa(calendar.hold_minutes)} دقیقه وقت داری پرداخت کنی.`
    : step === "crew"
      ? "سلام! بگو چند نفرید و چند سالشونه؛ خودم حساب می‌کنم چند تا خودرو لازمه."
      : step === "day"
        ? plan.ok
          ? `${karts(plan.singles, plan.doubles)} لازم دارید. کدوم روز میاید؟`
          : "اول ترکیب گروه رو درست کن."
        : step === "session"
          ? "هر سانس ۱۰ دقیقه‌ست. هر ساعتی که برای کل گروه جا داشته باشه رو می‌تونی بزنی."
          : customer.status === "signed-in"
            ? "همه‌چی آماده‌ست. برای ثبت، دکمه‌ی زرد پایین رو چند ثانیه نگه دار."
            : "فقط مونده ورود با شماره موبایل و پرداخت؛ بعدش بلیت برات پیامک میشه.";

  return (
    <div id="wizard-top" className="scroll-mt-20">
      {pendingHold && !reservation && (
        <Alert tone="warning" className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <span>
            بلیت شماره {fa(pendingHold.ticket_number)} ({fa(pendingHold.time)} {pendingHold.weekday}) هنوز پرداخت نشده و خودروهایش برای شما نگه داشته شده است.
          </span>
          <button type="button" className={buttonClasses("primary", "sm")} onClick={() => setReservation(pendingHold)}>
            ادامه پرداخت
          </button>
        </Alert>
      )}

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
                <p className="text-sm font-bold text-fg-subtle">
                  قدم {fa(stepIndex + 1)} از {fa(STEPS.length)}
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
              {(step === "day" || step === "session") && plan.ok && (
                <CrewChip
                  people={plan.people}
                  singles={plan.singles}
                  doubles={plan.doubles}
                  teens={manual ? null : crew.teen > 0 ? (teensDrive ? "خودشان می‌رانند" : "پشت بزرگسال") : null}
                  day={step === "session" && selectedDay ? `${selectedDay.weekday} ${dayAndMonth(selectedDay.date_jalali)} · ${toman(total)} تومان` : null}
                  onEdit={() => go("crew")}
                />
              )}

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
                    juniorWindow={juniorWindow}
                    onManualSingles={(v) => setManualSingles(Math.max(0, v))}
                    onManualDoubles={(v) => setManualDoubles(Math.max(0, v))}
                    maxKarts={maxKarts}
                    fromPrice={fromPrice}
                  />
                )}
                {step === "day" && <WeatherNote />}
                {step === "day" && (
                  <DayStep
                    days={calendar.days}
                    selected={date}
                    onSelect={chooseDate}
                    singles={plan.singles}
                    doubles={plan.doubles}
                    junior={juniorBound ? juniorWindow : null}
                    juniorWho={juniorWho}
                    onBlocked={(blocked, weekday) => setFix({ reason: "teen-day", date: blocked, label: weekday })}
                  />
                )}
                {step === "session" && (
                  <>
                    {dayError && <Alert tone="error">{dayError}</Alert>}
                    {!day && !dayError && (
                      <div role="status" className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                        <span className="sr-only">در حال خواندن جدول استارت</span>
                        {Array.from({ length: 9 }, (_, i) => (
                          <Skeleton key={i} className="h-24 rounded-2xl" />
                        ))}
                        <p aria-hidden="true" className="col-span-full pt-1 text-center text-sm text-on-carbon-muted">دارم جای خالی سانس‌ها را می‌شمارم…</p>
                      </div>
                    )}
                    {day && day.is_closed && <Alert tone="info">این روز رزرو آنلاین ندارد؛ روز دیگری را انتخاب کنید.</Alert>}
                    {day && !day.is_closed && (
                      <SessionStep
                        sessions={day.sessions}
                        selected={time}
                        onSelect={chooseTime}
                        singles={plan.singles}
                        doubles={plan.doubles}
                        junior={juniorBound ? juniorWindow : null}
                        onBlocked={(session, kind) =>
                          setFix(
                            kind === "teen"
                              ? { reason: "teen-time", time: session.time, label: fa(session.time) }
                              : { reason: "capacity", time: session.time, label: fa(session.time), singlesLeft: session.singles_left, doublesLeft: session.doubles_left },
                          )
                        }
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
                    accepted={accepted}
                    onAccept={setAccepted}
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

        {fix && (
          <FixSheet
            fix={fix}
            passengers={fix.reason === "capacity" ? null : passengersAlternative}
            need={{ singles: plan.singles, doubles: plan.doubles }}
            teenRule={juniorRule(juniorWindow, fa)}
            everyone={juniorWindow.everyone}
            onSeatTeens={seatTeensAndKeep}
            onEditCrew={editCrew}
            onClose={() => setFix(null)}
          />
        )}

        {/* Computers: the pit board beside the steps, with the lap and the pass filling in live. */}
        <aside className="hidden lg:col-span-5 lg:block">
          <div className="sticky top-28 space-y-5">
            <div className="carbon rounded-[1.75rem] border border-white/10 p-5">
              <p className="mb-3 text-sm font-black">مراحل رزرو شما</p>
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

/** The crew in one line at the top of the day and session steps, with a one-tap way back to change it. */
function CrewChip({ people, singles, doubles, teens, day = null, onEdit }: { people: number; singles: number; doubles: number; teens: string | null; day?: string | null; onEdit: () => void }) {
  return (
    <div className="mt-4 flex items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.035] px-4 py-2.5">
      <p className="min-w-0 text-sm leading-6">
        <span className="font-black">{fa(people)} نفر</span>
        <span className="text-fg-muted"> · {karts(singles, doubles)}</span>
        {teens && <span className="text-fg-muted"> · نوجوان‌ها {teens}</span>}
        {day && <span className="block font-bold text-accent">{day}</span>}
      </p>
      <button type="button" onClick={onEdit} className="shrink-0 rounded-full border border-white/15 px-3 py-1 text-xs font-bold text-accent transition hover:border-accent">
        تغییر نفرات
      </button>
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
  accepted: boolean;
  onAccept: (accepted: boolean) => void;
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
        {site.contact.phone && (
          <a href={site.contact.phone.href} className={buttonClasses("primary", "lg", "w-full")}>
            <PhoneIcon className="h-5 w-5" />
            تماس برای رزرو این سانس
          </a>
        )}
        <p className="text-center text-sm text-fg-muted">پرداخت آنلاین به‌زودی فعال می‌شود؛ فعلاً با پشتیبانی تماس بگیرید.</p>
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
          <TermsPledge accepted={props.accepted} onChange={props.onAccept} />
          <LaunchButton key={props.launchAttempt} onLaunch={() => props.onLaunch(props.signedInMe!)} busy={props.busy} disabled={!props.accepted} />
          {!props.accepted && <p className="text-center text-xs font-bold text-fg-muted">برای ثبت، اول تیک تأیید را بزنید.</p>}
          <p className="text-center text-xs leading-6 text-fg-muted">
            خودروها {fa(props.holdMinutes)} دقیقه برای پرداخت نگه داشته می‌شوند. مبلغ نهایی را سرور حساب می‌کند.
          </p>
        </>
      ) : props.loading ? (
        <div role="status" className="space-y-3">
          <span className="sr-only">در حال بررسی ورود</span>
          <Skeleton className="h-6 w-48 rounded-lg" />
          <Skeleton className="h-14 rounded-2xl" />
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
          <h2 id="held-title" className="text-[clamp(1.6rem,5vw,2.4rem)] font-black leading-tight">
            خودروها برای شما نگه داشته شد
          </h2>
          <p className="mt-2 text-sm text-fg-muted">فقط مونده پرداخت؛ بعدش بلیتتان قطعی می‌شود.</p>
        </div>
      </div>
      <TeamRadio message={props.radio} />
      <RacePass
        dayLabel={`${reservation.weekday} ${jalali(reservation.date_jalali)}`}
        time={reservation.time}
        singles={reservation.single_count}
        doubles={reservation.double_count}
        total={reservation.amount_toman}
        name={reservation.contact_name || props.name}
        ticket={reservation.ticket_number}
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
      <p className="mt-4 text-on-carbon-muted">برای رزرو با پشتیبانی تماس بگیرید.</p>
      {site.contact.phone && (
        <a href={site.contact.phone.href} className={buttonClasses("primary", "lg", "mt-8")}>
          <PhoneIcon className="h-5 w-5" />
          تماس برای رزرو
        </a>
      )}
      <p className="mt-6 text-sm text-on-carbon-muted">
        <Link href={hrefFor("/faq", SPLIT_HOSTS)} className="underline underline-offset-4">
          سوالات متداول
        </Link>
      </p>
    </div>
  );
}

/** "1405/07/28" -> "۲۸ مهر": how people say a date. */
function dayAndMonth(dateJalali: string): string {
  const [, month, day] = dateJalali.split("/").map(Number);
  return `${fa(day)} ${JALALI_MONTHS[month - 1] ?? ""}`;
}
