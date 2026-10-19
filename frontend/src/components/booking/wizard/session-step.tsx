"use client";

import { fa } from "@/lib/format";
import type { SessionAvailability } from "@/lib/types";
import { juniorSession, sessionMinutes, type JuniorWindow } from "@/components/booking/wizard/crew";

const PERIODS = [
  { title: "صبح", from: 0, to: 12 * 60 },
  { title: "ظهر", from: 12 * 60, to: 15 * 60 },
  { title: "عصر", from: 15 * 60, to: 18 * 60 },
  { title: "شب", from: 18 * 60, to: 21 * 60 },
  { title: "آخر شب", from: 21 * 60, to: 30 * 60 },
] as const;

/** The sky over the track at that hour: late-afternoon sun, sunset, then floodlit night. */
function skyFor(time: string): string {
  const m = sessionMinutes(time);
  if (m < 12 * 60) return "linear-gradient(160deg, rgb(120 200 255 / 0.22), rgb(255 230 150 / 0.08) 55%, transparent)";
  if (m < 17 * 60) return "linear-gradient(160deg, rgb(255 196 0 / 0.28), rgb(255 120 40 / 0.08) 55%, transparent)";
  if (m < 19 * 60) return "linear-gradient(160deg, rgb(255 90 40 / 0.32), rgb(170 40 120 / 0.12) 55%, transparent)";
  if (m < 22 * 60) return "linear-gradient(160deg, rgb(80 90 255 / 0.28), rgb(20 30 90 / 0.15) 55%, transparent)";
  return "linear-gradient(160deg, rgb(120 70 255 / 0.25), rgb(10 10 40 / 0.2) 55%, transparent)";
}

/** "closed" and "full" cannot be helped; "teen" and "capacity" open the fix sheet when tapped. */
type Fit = { fits: boolean; kind: "ok" | "closed" | "full" | "teen" | "capacity"; reason: string };

function fitFor(session: SessionAvailability, singles: number, doubles: number, junior: JuniorWindow | null): Fit {
  if (!session.bookable) return { fits: false, kind: "closed", reason: "بسته" };
  if (session.singles_left + session.doubles_left === 0) return { fits: false, kind: "full", reason: "تکمیل" };
  if (junior !== null && !juniorSession(session.time, junior)) return { fits: false, kind: "teen", reason: "خارج از ساعت زیر ۱۵ سال · بزنید" };
  if (session.singles_left < singles || session.doubles_left < doubles) {
    return { fits: false, kind: "capacity", reason: `فقط ${fa(session.singles_left)} تک و ${fa(session.doubles_left)} دونفره · بزنید` };
  }
  return { fits: true, kind: "ok", reason: "" };
}

type SessionStepProps = {
  /** Online booking has closed for today (the daily cutoff), so every session reads as closed. */
  cutoffPassed: boolean;
  sessions: SessionAvailability[];
  selected: string | null;
  onSelect: (time: string) => void;
  singles: number;
  doubles: number;
  /** The under-15 hours when they bind this crew, else null. */
  junior: JuniorWindow | null;
  /** A session that cannot take the crew as it is was tapped. */
  onBlocked: (session: SessionAvailability, kind: "teen" | "capacity") => void;
};

/**
 * Step 3: the session, drawn as a starting grid. Every kart of the session is a grid box; the crew's karts light up in
 * free boxes. Sessions that cannot take the whole crew stay visible but dimmed, with the reason.
 */
export function SessionStep({ cutoffPassed, sessions, selected, onSelect, singles, doubles, junior, onBlocked }: SessionStepProps) {
  const fitting = sessions.filter((s) => fitFor(s, singles, doubles, junior).fits).length;
  const message =
    fitting > 0
      ? `${fa(fitting)} سانس برای کل گروه شما جا دارد.`
      : cutoffPassed
        ? "رزرو آنلاین تا نیمه‌شب بسته است؛ جدول را ببینید و از نیمه‌شب ثبت کنید."
        : "هیچ سانسی در این روز برای کل گروه جا ندارد؛ روز دیگری را امتحان کنید.";
  return (
    <div className="space-y-7">
      <p className="text-sm text-fg-muted" aria-live="polite">
        {message}
      </p>
      <nav aria-label="پرش به بخشی از روز" className="sticky top-[4.25rem] z-10 -mx-1 flex gap-2 overflow-x-auto bg-[#0b0c0f]/85 px-1 py-2 backdrop-blur">
        {PERIODS.map((period) => {
          const inPeriod = sessions.filter((s) => sessionMinutes(s.time) >= period.from && sessionMinutes(s.time) < period.to);
          if (inPeriod.length === 0) return null;
          const open = inPeriod.filter((s) => fitFor(s, singles, doubles, junior).fits).length;
          return (
            <a
              key={period.title}
              href={`#period-${period.from}`}
              onClick={(event) => {
                event.preventDefault();
                document.getElementById(`period-${period.from}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
              }}
              className={`shrink-0 rounded-full px-4 py-2 text-sm font-bold ring-1 transition-colors ${open > 0 ? "ring-white/20 hover:ring-accent" : "text-fg-subtle ring-white/10"}`}
            >
              {period.title}
              <span className="ms-1.5 text-xs text-fg-muted">{open > 0 ? `${fa(open)} خالی` : "پر"}</span>
            </a>
          );
        })}
      </nav>
      {PERIODS.map((period) => {
        const inPeriod = sessions.filter((s) => sessionMinutes(s.time) >= period.from && sessionMinutes(s.time) < period.to);
        if (inPeriod.length === 0) return null;
        return (
          <section key={period.title} id={`period-${period.from}`} aria-label={`سانس‌های ${period.title}`} className="scroll-mt-32">
            <h3 className="mb-3 flex items-center gap-3 text-sm font-black text-fg-muted">
              {period.title}
              <span aria-hidden="true" className="h-px flex-1 bg-white/10" />
            </h3>
            <div role="radiogroup" aria-label={`سانس‌های ${period.title}`} className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
              {inPeriod.map((session) => (
                <GridTile
                  key={session.time}
                  session={session}
                  active={session.time === selected}
                  fit={fitFor(session, singles, doubles, junior)}
                  singles={singles}
                  doubles={doubles}
                  onSelect={onSelect}
                  onBlocked={onBlocked}
                />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function GridTile({
  session,
  active,
  fit,
  singles,
  doubles,
  onSelect,
  onBlocked,
}: {
  session: SessionAvailability;
  active: boolean;
  fit: Fit;
  singles: number;
  doubles: number;
  onSelect: (time: string) => void;
  onBlocked: (session: SessionAvailability, kind: "teen" | "capacity") => void;
}) {
  const fixable = fit.kind === "teen" || fit.kind === "capacity";
  const free = session.singles_left + session.doubles_left;
  const lastSeats = fit.fits && free <= 3;
  const takenSingles = session.single_capacity - session.singles_left;
  const takenDoubles = session.double_capacity - session.doubles_left;
  const label = fit.fits ? (lastSeats ? `فقط ${fa(free)} جا مانده` : `${fa(free)} جای خالی`) : fit.reason;
  return (
    <button
      type="button"
      role="radio"
      aria-checked={active}
      disabled={!fit.fits && !fixable}
      onClick={() => (fit.fits ? onSelect(session.time) : fixable && onBlocked(session, fit.kind as "teen" | "capacity"))}
      aria-label={`سانس ساعت ${fa(session.time)}، ${label}`}
      className={`edge-glow relative overflow-hidden rounded-3xl border p-3.5 text-right transition-all duration-300 ease-out-expo ${
        active
          ? "border-accent shadow-[0_0_0_1px_var(--color-accent),0_20px_40px_-18px_rgb(255_196_0/0.6)]"
          : fit.fits
            ? "border-white/10 hover:-translate-y-0.5 hover:border-white/30"
            : fixable
              ? "border-dashed border-white/15 opacity-75 hover:border-accent/50 hover:opacity-100"
              : "cursor-not-allowed border-dashed border-white/10 opacity-40"
      }`}
    >
      <span aria-hidden="true" className="absolute inset-0 -z-10 bg-[#0d0e12]" />
      <span aria-hidden="true" className="absolute inset-0 -z-10 opacity-90" style={{ background: skyFor(session.time) }} />
      <span className="flex items-center justify-between gap-2">
        <span className="text-[1.65rem] font-black leading-none">{fa(session.time)}</span>
        {active && <span className="rounded-full bg-accent px-2 py-0.5 text-[0.65rem] font-black text-ink">انتخاب شما</span>}
        {!active && lastSeats && <span className="pulse-dot" aria-hidden="true" />}
      </span>
      {/* The starting grid: staggered boxes, two columns, like the grid painted on the track. */}
      <span className="mt-3 grid grid-cols-2 gap-x-2 gap-y-1" aria-hidden="true">
        {Array.from({ length: session.single_capacity }, (_, i) => {
          const taken = i < takenSingles;
          const yours = fit.fits && !taken && i - takenSingles < singles;
          return <GridBox key={`s${i}`} state={taken ? "taken" : yours ? "yours" : "free"} offset={i % 2 === 1} />;
        })}
        {Array.from({ length: session.double_capacity }, (_, i) => {
          const taken = i < takenDoubles;
          const yours = fit.fits && !taken && i - takenDoubles < doubles;
          return <GridBox key={`d${i}`} state={taken ? "taken" : yours ? "yours" : "free"} offset={i % 2 === 1} double />;
        })}
      </span>
      <span className={`mt-3 block text-xs font-bold ${active || fixable ? "text-accent" : lastSeats ? "text-[#ff8a7e]" : "text-fg-muted"}`}>{label}</span>
    </button>
  );
}

function GridBox({ state, offset, double = false }: { state: "taken" | "free" | "yours"; offset: boolean; double?: boolean }) {
  return (
    <span
      className={`block h-2.5 rounded-[3px] border transition-colors duration-300 ${offset ? "translate-y-1" : ""} ${
        state === "taken"
          ? "border-transparent bg-white/15"
          : state === "yours"
            ? "border-accent bg-accent shadow-[0_0_10px_rgb(255_196_0/0.8)]"
            : "border-white/35 bg-transparent"
      } ${double ? "h-3.5" : ""}`}
    />
  );
}
