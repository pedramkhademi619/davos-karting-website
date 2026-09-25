"use client";

import { fa, jalaliParts } from "@/lib/format";
import type { BookableDay } from "@/lib/types";

type DayStripProps = {
  days: BookableDay[];
  selected: string | null;
  onSelect: (date: string) => void;
};

/** The bookable days as big date cards (Jalali day and month, weekday, holiday badge). */
export function DayStrip({ days, selected, onSelect }: DayStripProps) {
  return (
    <div role="radiogroup" aria-label="انتخاب روز" className="flex gap-3 overflow-x-auto pb-2">
      {days.map((day) => {
        const active = day.date === selected;
        const { day: dayNumber, month } = jalaliParts(day.date);
        return (
          <button
            key={day.date}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onSelect(day.date)}
            className={`relative flex min-w-[8.5rem] shrink-0 flex-col items-center rounded-3xl border-2 px-5 py-4 text-center transition-all duration-300 ease-out-expo ${
              active
                ? "carbon border-accent shadow-[0_18px_40px_-20px_rgb(12_13_16/0.9)]"
                : "border-line bg-surface hover:-translate-y-0.5 hover:border-fg"
            }`}
          >
            <span className={`text-sm font-bold ${active ? "text-accent" : "text-fg-muted"}`}>{day.weekday}</span>
            <span className="mt-1 text-4xl font-black leading-none">{dayNumber}</span>
            <span className={`mt-1 text-sm font-bold ${active ? "text-on-carbon-muted" : "text-fg-subtle"}`}>{month}</span>
            {day.is_holiday && (
              <span className="absolute -top-2 left-3 rounded-full bg-signal px-2 py-0.5 text-[0.65rem] font-black text-white">تعطیل</span>
            )}
            <span className="sr-only">{fa(day.date_jalali)}</span>
          </button>
        );
      })}
    </div>
  );
}
