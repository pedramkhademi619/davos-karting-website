"use client";

import { monthName, monthOf, shiftMonth, type JalaliMonth } from "@/lib/accounting";
import { currentBusinessDay } from "@/lib/jalali";

/** ‹ مهر ۱۴۰۵ › : steps through Jalali months, never past the current one. */
export function MonthStepper({ month, onChange }: { month: JalaliMonth; onChange: (month: JalaliMonth) => void }) {
  const now = monthOf(currentBusinessDay());
  const atNow = month.year === now.year && month.month === now.month;
  const button = "grid h-11 w-11 place-items-center rounded-full text-xl font-black ring-1 ring-line-strong transition-colors hover:bg-surface-2 disabled:opacity-30";
  return (
    <div className="flex items-center justify-between gap-3 sm:justify-start">
      <button type="button" aria-label="ماه قبل" onClick={() => onChange(shiftMonth(month, -1))} className={button}>
        ‹
      </button>
      <p className="min-w-36 text-center text-lg font-black" aria-live="polite">
        {monthName(month)}
      </p>
      <button type="button" aria-label="ماه بعد" disabled={atNow} onClick={() => onChange(shiftMonth(month, 1))} className={button}>
        ›
      </button>
    </div>
  );
}
