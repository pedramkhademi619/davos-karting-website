"use client";

import type { ChangeEvent, ReactNode } from "react";
import { fa, toLatinDigits } from "@/lib/format";

export function Field({ label, hint, children }: { label: string; hint?: ReactNode; children: ReactNode }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-fg-subtle">{hint}</span>}
    </label>
  );
}

/** A Toman amount typed with any digits; shown grouped ("۱٬۲۵۰٬۰۰۰"). The value is a whole number of Toman. */
export function MoneyInput({
  label,
  value,
  onChange,
  hint,
  big = false,
  autoFocus = false,
}: {
  label: string;
  value: number;
  onChange: (toman: number) => void;
  hint?: ReactNode;
  big?: boolean;
  autoFocus?: boolean;
}) {
  const handle = (event: ChangeEvent<HTMLInputElement>) => {
    const digits = toLatinDigits(event.target.value).replace(/[^\d]/g, "");
    onChange(digits ? Math.min(Number(digits), 100_000_000_000_000) : 0);
  };
  return (
    <Field label={label} hint={hint}>
      <div className="relative">
        <input
          className={`field ${big ? "!h-16 !pl-16 !text-3xl font-black" : "!pl-14"}`}
          dir="ltr"
          inputMode="numeric"
          autoFocus={autoFocus}
          value={value ? fa(value.toLocaleString("en-US")).replace(/,/g, "٬") : ""}
          onChange={handle}
          placeholder="۰"
        />
        <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-sm font-bold text-fg-subtle">تومان</span>
      </div>
    </Field>
  );
}

/** A row of mutually exclusive pill buttons (e.g. صندوق / بانک). */
export function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { id: T; label: ReactNode }[];
  value: T;
  onChange: (id: T) => void;
}) {
  return (
    <div role="radiogroup" aria-label={label}>
      <p className="label">{label}</p>
      <div className="flex gap-1 rounded-2xl bg-surface-2 p-1">
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            role="radio"
            aria-checked={value === option.id}
            onClick={() => onChange(option.id)}
            className={`min-h-11 flex-1 rounded-xl px-3 text-sm font-extrabold transition-colors ${value === option.id ? "bg-ink text-white shadow-sm" : "text-fg-muted hover:text-fg"}`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Pick one category from a wrap of chips. */
export function CategoryChips({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { id: string; name: string }[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <div role="radiogroup" aria-label={label}>
      <p className="label">{label}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            role="radio"
            aria-checked={value === option.id}
            onClick={() => onChange(option.id)}
            className={`rounded-full px-3.5 py-2 text-sm font-bold ring-1 transition-colors ${value === option.id ? "bg-ink text-white ring-ink" : "bg-surface text-fg-muted ring-line-strong hover:text-fg"}`}
          >
            {option.name}
          </button>
        ))}
      </div>
    </div>
  );
}
