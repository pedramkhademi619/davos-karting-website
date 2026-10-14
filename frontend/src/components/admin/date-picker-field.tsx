"use client";

import { useEffect, useRef, useState } from "react";
import { fa } from "@/lib/format";
import {
  JALALI_MONTHS,
  currentBusinessDay,
  isoToJalali,
  isoToJalaliParts,
  jalaliMonthLength,
  jalaliToIso,
  weekdayIndex,
} from "@/lib/jalali";

const WEEKDAY_SHORT = ["ش", "ی", "د", "س", "چ", "پ", "ج"];
const WEEKDAY_FULL = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"];

/** A Jalali month grid. `selected` days are highlighted; days before `minIso` cannot be picked (unless selected). */
function MonthCalendar({
  selected,
  onPick,
  minIso,
  startIso,
}: {
  selected: ReadonlySet<string>;
  onPick: (iso: string) => void;
  minIso?: string;
  startIso: string;
}) {
  const today = currentBusinessDay();
  const start = isoToJalaliParts(startIso);
  const [month, setMonth] = useState({ jy: start.jy, jm: start.jm });

  const length = jalaliMonthLength(month.jy, month.jm);
  const offset = weekdayIndex(jalaliToIso(month.jy, month.jm, 1));
  const cells: (string | null)[] = [
    ...Array<null>(offset).fill(null),
    ...Array.from({ length }, (_, i) => jalaliToIso(month.jy, month.jm, i + 1)),
  ];

  const shift = (delta: number) =>
    setMonth(({ jy, jm }) => {
      const index = jy * 12 + (jm - 1) + delta;
      return { jy: Math.floor(index / 12), jm: (index % 12) + 1 };
    });

  return (
    <div className="rounded-2xl border border-line-strong bg-surface p-3">
      <div className="mb-2 flex items-center justify-between">
        <button type="button" onClick={() => shift(1)} aria-label="ماه بعد" className="grid h-9 w-9 place-items-center rounded-full hover:bg-surface-2">
          ‹
        </button>
        <p className="font-black">
          {JALALI_MONTHS[month.jm - 1]} {fa(month.jy)}
        </p>
        <button type="button" onClick={() => shift(-1)} aria-label="ماه قبل" className="grid h-9 w-9 place-items-center rounded-full hover:bg-surface-2">
          ›
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs text-fg-subtle">
        {WEEKDAY_SHORT.map((d) => (
          <span key={d} className="py-1 font-bold">
            {d}
          </span>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {cells.map((iso, index) => {
          if (!iso) return <span key={`blank-${index}`} />;
          const on = selected.has(iso);
          return (
            <button
              key={iso}
              type="button"
              disabled={minIso !== undefined && iso < minIso && !on}
              aria-pressed={on}
              aria-label={isoToJalali(iso)}
              onClick={() => onPick(iso)}
              className={`h-10 rounded-xl text-sm font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-30 ${
                on ? "bg-ink text-accent" : "hover:bg-surface-2"
              } ${iso === today && !on ? "ring-2 ring-accent" : ""}`}
            >
              {fa(index - offset + 1)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Picks any number of dates on a Jalali calendar (click a day to add it, click again to remove it), so nobody has to
 * type a date. Days before today cannot be added; dates already stored stay listed and can be removed.
 */
export function DatePickerField({ value, onChange }: { value: string[]; onChange: (dates: string[]) => void }) {
  const today = currentBusinessDay();
  const toggle = (iso: string) => onChange(value.includes(iso) ? value.filter((d) => d !== iso) : [...value, iso].sort());

  return (
    <div>
      <MonthCalendar selected={new Set(value)} onPick={toggle} minIso={today} startIso={today} />
      {value.length === 0 ? (
        <p className="mt-3 text-sm text-fg-subtle">هنوز تاریخی انتخاب نشده است.</p>
      ) : (
        <ul className="mt-3 flex flex-wrap gap-2">
          {value.map((iso) => (
            <li key={iso} className="flex items-center gap-2 rounded-full bg-surface-2 py-1 pl-1 pr-4 text-sm font-bold">
              {WEEKDAY_FULL[weekdayIndex(iso)]} {fa(isoToJalali(iso))}
              <button
                type="button"
                onClick={() => toggle(iso)}
                aria-label={`حذف ${isoToJalali(iso)}`}
                className="grid h-7 w-7 place-items-center rounded-full hover:bg-line-strong"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** One date chosen from a calendar that opens under the button; any day, past or future. */
export function SingleDatePicker({ value, onChange, label }: { value: string; onChange: (iso: string) => void; label: string }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !box.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <div ref={box} className="relative">
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={label}
        onClick={() => setOpen((v) => !v)}
        className="field flex h-10 w-44 items-center justify-between gap-2 text-sm font-bold"
      >
        <span>
          {WEEKDAY_FULL[weekdayIndex(value)]} {fa(isoToJalali(value))}
        </span>
        <span aria-hidden="true">▾</span>
      </button>
      {open && (
        <div role="dialog" aria-label={label} className="absolute right-0 z-30 mt-2 w-72 shadow-xl">
          <MonthCalendar
            selected={new Set([value])}
            startIso={value}
            onPick={(iso) => {
              onChange(iso);
              setOpen(false);
            }}
          />
        </div>
      )}
    </div>
  );
}
