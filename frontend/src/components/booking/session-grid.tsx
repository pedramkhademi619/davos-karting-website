"use client";

import { fa } from "@/lib/format";
import type { SessionAvailability } from "@/lib/types";

type SessionGridProps = {
  sessions: SessionAvailability[];
  selected: string | null;
  onSelect: (time: string) => void;
};

const PERIODS = [
  { title: "عصر", from: 0, to: 18 * 60 },
  { title: "شب", from: 18 * 60, to: 21 * 60 },
  { title: "آخر شب", from: 21 * 60, to: 24 * 60 + 6 * 60 },
] as const;

/** Minutes since the business day's start; times after midnight (00:15 ... 05:59) belong to the same evening. */
function minutes(time: string): number {
  const [h, m] = time.split(":").map(Number);
  const value = h * 60 + m;
  return h < 6 ? value + 24 * 60 : value;
}

/** Cinema-style seat map: one tile per session with a dot per kart, grouped into evening periods. */
export function SessionGrid({ sessions, selected, onSelect }: SessionGridProps) {
  return (
    <div className="space-y-8">
      {PERIODS.map((period) => {
        const inPeriod = sessions.filter((s) => minutes(s.time) >= period.from && minutes(s.time) < period.to);
        if (inPeriod.length === 0) return null;
        return (
          <section key={period.title} aria-label={`سانس‌های ${period.title}`}>
            <h3 className="mb-3 flex items-center gap-3 text-sm font-black text-fg-muted">
              {period.title}
              <span aria-hidden="true" className="h-px flex-1 bg-line" />
            </h3>
            <div role="radiogroup" aria-label={`سانس‌های ${period.title}`} className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
              {inPeriod.map((session) => (
                <SessionTile key={session.time} session={session} active={session.time === selected} onSelect={onSelect} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function SessionTile({ session, active, onSelect }: { session: SessionAvailability; active: boolean; onSelect: (time: string) => void }) {
  const free = session.singles_left + session.doubles_left;
  const available = session.bookable && free > 0;
  const lastSeats = available && free <= 2;
  const status = !session.bookable ? "بسته" : free === 0 ? "تکمیل" : lastSeats ? `فقط ${fa(free)} جا` : `${fa(free)} جای خالی`;

  return (
    <button
      type="button"
      role="radio"
      aria-checked={active}
      disabled={!available}
      onClick={() => onSelect(session.time)}
      aria-label={`سانس ساعت ${fa(session.time)}، ${status}`}
      className={`group relative flex flex-col gap-3 rounded-2xl border-2 p-4 text-right transition-all duration-300 ease-out-expo ${
        active
          ? "carbon pop border-accent shadow-[0_18px_40px_-18px_rgb(12_13_16/0.85)]"
          : available
            ? `border-line bg-surface hover:-translate-y-0.5 hover:border-fg ${lastSeats ? "last-seats border-signal/50" : ""}`
            : "cursor-not-allowed border-dashed border-line bg-surface-2 opacity-60"
      }`}
    >
      <span className="flex items-center justify-between gap-2">
        <span className="text-2xl font-black leading-none">{fa(session.time)}</span>
        {lastSeats && !active && <span className="h-2 w-2 rounded-full bg-signal" aria-hidden="true" />}
      </span>
      <span className="flex flex-wrap items-center gap-1" aria-hidden="true">
        {Array.from({ length: session.single_capacity }, (_, i) => (
          <span key={`s${i}`} className={`seat-dot ${i < session.singles_left ? "" : "is-taken"}`} />
        ))}
        {Array.from({ length: session.double_capacity }, (_, i) => (
          <span key={`d${i}`} className={`seat-dot is-double ${i < session.doubles_left ? "" : "is-taken"}`} />
        ))}
      </span>
      <span className={`text-xs font-bold ${active ? "text-accent" : lastSeats ? "text-signal" : "text-fg-muted"}`}>{status}</span>
    </button>
  );
}
