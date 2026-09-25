"use client";

import { MinusIcon, PlusIcon } from "@/components/icons";
import { fa, toman } from "@/lib/format";

type KartStepperProps = {
  label: string;
  hint: string;
  price: number;
  value: number;
  max: number;
  onChange: (value: number) => void;
};

/** A − / + counter with big touch targets; announces the new count to screen readers. */
export function KartStepper({ label, hint, price, value, max, onChange }: KartStepperProps) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl bg-white/[0.06] p-4 ring-1 ring-white/10">
      <div>
        <p className="font-black">{label}</p>
        <p className="text-xs text-on-carbon-muted">{hint}</p>
        <p className="mt-1 text-sm font-bold text-accent">{toman(price)}</p>
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => onChange(Math.max(0, value - 1))}
          disabled={value <= 0}
          aria-label={`کم کردن ${label}`}
          className="grid h-11 w-11 place-items-center rounded-full border border-white/20 transition-colors hover:border-accent hover:text-accent disabled:opacity-30"
        >
          <MinusIcon className="h-5 w-5" />
        </button>
        <output aria-live="polite" className="w-8 text-center text-2xl font-black">
          {fa(value)}
        </output>
        <button
          type="button"
          onClick={() => onChange(Math.min(max, value + 1))}
          disabled={value >= max}
          aria-label={`افزودن ${label}`}
          className="grid h-11 w-11 place-items-center rounded-full bg-accent text-ink transition-transform active:scale-90 disabled:bg-white/10 disabled:text-on-carbon-muted"
        >
          <PlusIcon className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
