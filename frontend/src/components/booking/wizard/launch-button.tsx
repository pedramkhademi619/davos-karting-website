"use client";

import { useEffect, useRef, useState } from "react";

const HOLD_MS = 1500;
const LAMPS = 5;

/**
 * Launch control: press and hold, five red lights come on one by one, and when they go out the booking is sent. Letting
 * go early cancels, so a stray tap never books. A keyboard or screen-reader "click" (no pointer) confirms straight away.
 */
export function LaunchButton({ onLaunch, disabled, busy }: { onLaunch: () => void; disabled?: boolean; busy?: boolean }) {
  const [held, setHeld] = useState(0); // 0..1
  const [fired, setFired] = useState(false);
  const started = useRef<number | null>(null);
  const frame = useRef(0);
  const lastLamp = useRef(0);

  useEffect(() => () => cancelAnimationFrame(frame.current), []);

  function fire() {
    setFired(true);
    setHeld(1);
    if ("vibrate" in navigator) navigator.vibrate?.([30, 60, 120]);
    window.setTimeout(onLaunch, 260);
  }

  function start() {
    if (disabled || busy || fired) return;
    started.current = performance.now();
    lastLamp.current = 0;
    const tick = (now: number) => {
      if (started.current === null) return;
      const p = Math.min(1, (now - started.current) / HOLD_MS);
      setHeld(p);
      const lamp = Math.floor(p * LAMPS);
      if (lamp > lastLamp.current) {
        lastLamp.current = lamp;
        if ("vibrate" in navigator) navigator.vibrate?.(18);
      }
      if (p >= 1) {
        started.current = null;
        fire();
        return;
      }
      frame.current = requestAnimationFrame(tick);
    };
    frame.current = requestAnimationFrame(tick);
  }

  function stop() {
    if (started.current === null) return;
    started.current = null;
    cancelAnimationFrame(frame.current);
    setHeld(0);
  }

  const lit = fired ? 0 : Math.floor(held * LAMPS + 0.0001);
  const label = busy ? "در حال ثبت..." : fired ? "چراغ‌ها خاموش! رفتیم" : held > 0 ? "نگه دارید..." : "برای ثبت، دکمه را نگه دارید";
  return (
    <button
      type="button"
      disabled={disabled || busy}
      onPointerDown={(event) => {
        try {
          event.currentTarget.setPointerCapture(event.pointerId); // keep receiving "up" even if the finger slides off
        } catch {
          // Some browsers refuse capture for synthetic or already-released pointers; holding still works.
        }
        start();
      }}
      onPointerUp={stop}
      onPointerCancel={stop}
      onClick={(event) => {
        if (event.detail === 0 && !fired && !busy) fire();
      }}
      onContextMenu={(event) => event.preventDefault()}
      aria-label="ثبت و نگه داشتن خودروها"
      className="launch-button group relative w-full touch-none select-none overflow-hidden rounded-[1.6rem] border border-white/10 bg-[#0c0d10] p-4 text-on-carbon disabled:opacity-50"
    >
      <span aria-hidden="true" className="absolute inset-y-0 right-0 bg-accent/15 transition-[width] duration-75" style={{ width: `${held * 100}%` }} />
      <span className="relative flex items-center justify-between gap-4">
        <span className="flex gap-2" dir="ltr" aria-hidden="true">
          {Array.from({ length: LAMPS }, (_, i) => (
            <span key={i} className={`launch-lamp ${i < lit ? "is-on" : ""} ${fired ? "is-out" : ""}`} />
          ))}
        </span>
        <span className="text-left">
          <span className="block text-base font-black sm:text-lg">{label}</span>
          <span className="block text-xs text-on-carbon-muted">لانچ کنترل</span>
        </span>
      </span>
    </button>
  );
}
