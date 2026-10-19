"use client";

import { useEffect, useState } from "react";

/**
 * The race engineer on the team radio: one short line per step, typed out like a live transmission. Purely a guide; the
 * same information is on the screen in plain form, so it is hidden from screen readers.
 */
export function TeamRadio({ message }: { message: string }) {
  const [shown, setShown] = useState(message);
  const [typed, setTyped] = useState(message.length);

  // Restart the typing when the message changes (state is reset during render, the timer runs in the effect).
  if (shown !== message) {
    setShown(message);
    setTyped(0);
  }

  useEffect(() => {
    if (typed >= shown.length) return;
    // With reduced motion the whole line appears at once (still from a timer, never synchronously in the effect).
    const instant = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const timer = window.setTimeout(() => setTyped((n) => (instant ? shown.length : Math.min(shown.length, n + 2))), instant ? 0 : 22);
    return () => window.clearTimeout(timer);
  }, [typed, shown]);

  return (
    <div aria-hidden="true" className="glass flex items-center gap-3 rounded-2xl px-3.5 py-2.5">
      <span className="flex h-8 shrink-0 items-end gap-[3px]">
        {[0, 1, 2, 3, 4].map((i) => (
          <span
            key={i}
            className={`radio-bar w-[3px] rounded-full bg-accent ${typed < shown.length ? "is-live" : ""}`}
            style={{ ["--i" as string]: i, height: `${[40, 75, 100, 60, 30][i]}%` }}
          />
        ))}
      </span>
      <p className="min-w-0 text-[0.92rem] leading-7">
        {shown.slice(0, typed)}
        {typed < shown.length && <span className="ms-0.5 inline-block h-4 w-[2px] translate-y-0.5 bg-accent" />}
      </p>
    </div>
  );
}
