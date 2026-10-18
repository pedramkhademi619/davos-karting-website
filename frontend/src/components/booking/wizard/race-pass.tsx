"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { LogoMark } from "@/components/logo";
import { KartGlyph } from "@/components/booking/wizard/crew-step";
import { fa, toman } from "@/lib/format";

type RacePassProps = {
  dayLabel: string;
  time: string | null;
  singles: number;
  doubles: number;
  total: number;
  name: string;
  /** The reservation code once the karts are held; until then the pass is a preview. */
  code?: string;
  footer?: ReactNode;
};

/**
 * The booking as a holographic race pass. The foil follows the pointer on a computer and the phone's tilt on Android
 * (iOS asks permission for motion, so there it just shimmers on its own).
 */
export function RacePass({ dayLabel, time, singles, doubles, total, name, code, footer }: RacePassProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const card = ref.current;
    if (!card || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const set = (x: number, y: number) => {
      card.style.setProperty("--mx", `${(x * 100).toFixed(1)}%`);
      card.style.setProperty("--my", `${(y * 100).toFixed(1)}%`);
      card.style.setProperty("--rx", `${((0.5 - y) * 10).toFixed(2)}deg`);
      card.style.setProperty("--ry", `${((x - 0.5) * 14).toFixed(2)}deg`);
    };
    const onMove = (event: PointerEvent) => {
      const box = card.getBoundingClientRect();
      set((event.clientX - box.left) / box.width, (event.clientY - box.top) / box.height);
    };
    const onLeave = () => set(0.5, 0.5);
    const onTilt = (event: DeviceOrientationEvent) => {
      if (event.beta === null || event.gamma === null) return;
      set(Math.min(1, Math.max(0, 0.5 + event.gamma / 60)), Math.min(1, Math.max(0, 0.5 + (event.beta - 40) / 60)));
    };
    card.addEventListener("pointermove", onMove);
    card.addEventListener("pointerleave", onLeave);
    window.addEventListener("deviceorientation", onTilt);
    return () => {
      card.removeEventListener("pointermove", onMove);
      card.removeEventListener("pointerleave", onLeave);
      window.removeEventListener("deviceorientation", onTilt);
    };
  }, []);

  const bays = [...Array(Math.min(singles, 8)).fill(false), ...Array(Math.min(doubles, 8)).fill(true)] as boolean[];
  return (
    <div className="[perspective:1200px]">
      <div ref={ref} className="race-pass relative overflow-hidden rounded-[1.75rem] p-5 text-on-carbon sm:p-6">
        <div aria-hidden="true" className="race-pass-foil" />
        <div className="relative flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <LogoMark className="h-10 w-10 shrink-0" />
            <div>
              <p className="text-xs font-bold text-on-carbon-muted">پاس ورود پیست</p>
              <p className="race-number whitespace-nowrap text-xs font-bold tracking-[0.18em] sm:text-sm sm:tracking-[0.25em]" dir="ltr">
                DAVOS KARTING
              </p>
            </div>
          </div>
          <span className={`shrink-0 whitespace-nowrap rounded-full px-2.5 py-1 text-[0.65rem] font-black ${code ? "bg-go text-ink" : "bg-white/10 text-on-carbon-muted"}`}>
            {code ? "نگه داشته شد" : "پیش‌نمایش"}
          </span>
        </div>

        <div className="relative mt-6 grid grid-cols-[1fr_auto] items-end gap-4">
          <div className="min-w-0">
            <p className="text-xs text-on-carbon-muted">راننده</p>
            <p className="truncate text-xl font-black">{name.trim() || "مهمان پیست"}</p>
          </div>
          <div className="text-left">
            <p className="text-xs text-on-carbon-muted">سانس</p>
            <p className="race-number text-3xl font-black leading-none text-accent" dir="ltr">
              {time ? fa(time) : "--:--"}
            </p>
          </div>
        </div>

        <div className="relative mt-4 flex items-center justify-between gap-3 border-t border-dashed border-white/15 pt-4">
          <p className="font-black">{dayLabel || "روز را انتخاب کنید"}</p>
          <p className="font-black text-accent">{total > 0 ? toman(total) : ""}</p>
        </div>

        {bays.length > 0 && (
          <div className="relative mt-4 flex flex-wrap gap-1.5" aria-hidden="true">
            {bays.map((double, index) => (
              <span key={index} className="grid h-9 place-items-center rounded-xl bg-black/35 px-1.5">
                <KartGlyph double={double} className="h-6 w-8" />
              </span>
            ))}
          </div>
        )}

        <div className="relative mt-5 flex items-center justify-between gap-3">
          <span className="race-number text-lg font-black tracking-[0.18em]" dir="ltr">
            {code ?? "• • • • • •"}
          </span>
          <span aria-hidden="true" className="barcode h-8 w-28" />
        </div>
        {footer && <div className="relative mt-5">{footer}</div>}
      </div>
    </div>
  );
}
