"use client";

import { fa, jalaliParts, toman } from "@/lib/format";
import type { BookableDay } from "@/lib/types";
import { TEEN_DAYS } from "@/components/booking/wizard/crew";

type DayStepProps = {
  days: BookableDay[];
  selected: string | null;
  onSelect: (date: string) => void;
  singles: number;
  doubles: number;
  teenDrivers: number;
};

/**
 * Step 2: the day. Each card already shows what the whole crew pays that day, and days the teens may not drive on are
 * set aside with the reason.
 */
export function DayStep({ days, selected, onSelect, singles, doubles, teenDrivers }: DayStepProps) {
  return (
    <div role="radiogroup" aria-label="انتخاب روز" className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-4">
      {days.map((day, index) => {
        const active = day.date === selected;
        const blockedForTeens = teenDrivers > 0 && !TEEN_DAYS.has(day.weekday);
        const price = singles * day.single_price_toman + doubles * day.double_price_toman;
        const { day: dayNumber, month } = jalaliParts(day.date);
        return (
          <button
            key={day.date}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={blockedForTeens}
            onClick={() => onSelect(day.date)}
            className={`edge-glow group relative overflow-hidden rounded-3xl border p-4 text-right transition-all duration-300 ease-out-expo ${
              active
                ? "border-accent bg-accent text-ink shadow-[0_18px_40px_-16px_rgb(255_196_0/0.7)]"
                : blockedForTeens
                  ? "cursor-not-allowed border-dashed border-white/10 bg-white/[0.02] opacity-50"
                  : "border-white/10 bg-white/[0.035] hover:-translate-y-0.5 hover:border-white/25"
            }`}
          >
            <span className="flex items-center justify-between gap-2">
              <span className={`text-sm font-bold ${active ? "text-ink/75" : "text-fg-muted"}`}>
                {index === 0 ? "نزدیک‌ترین" : day.weekday}
              </span>
              {day.is_holiday && (
                <span className={`rounded-full px-2 py-0.5 text-[0.62rem] font-black ${active ? "bg-ink text-accent" : "bg-signal text-white"}`}>
                  تعطیل
                </span>
              )}
            </span>
            <span className="mt-2 flex items-baseline gap-2">
              <span className="text-4xl font-black leading-none">{dayNumber}</span>
              <span className={`text-sm font-bold ${active ? "text-ink/75" : "text-fg-subtle"}`}>{month}</span>
            </span>
            {index === 0 && <span className={`mt-1 block text-xs ${active ? "text-ink/70" : "text-fg-subtle"}`}>{day.weekday}</span>}
            <span className={`mt-3 block border-t pt-2 text-xs font-bold ${active ? "border-ink/15" : "border-white/10"}`}>
              {blockedForTeens ? "نوجوان‌ها این روز نمی‌رانند" : price > 0 ? toman(price) : "—"}
            </span>
            <span className="sr-only">{fa(day.date_jalali)}</span>
          </button>
        );
      })}
    </div>
  );
}
