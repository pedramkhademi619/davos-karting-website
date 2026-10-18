"use client";

import { useEffect, useRef } from "react";
import { buttonClasses } from "@/components/button-link";
import { CloseIcon } from "@/components/icons";
import { fa, karts, toman } from "@/lib/format";

/** Why a day or session the customer tapped cannot take the crew as it is, and what was tapped. */
export type Fix =
  | { reason: "teen-day"; date: string; label: string }
  | { reason: "teen-time"; time: string; label: string }
  | { reason: "capacity"; time: string; label: string; singlesLeft: number; doublesLeft: number };

type Alternative = { ok: true; singles: number; doubles: number; price: number } | { ok: false; missingDrivers: number };

type FixSheetProps = {
  fix: Fix;
  /** The crew with the teens moved to the back seat, if that is possible. */
  passengers: Alternative | null;
  need: { singles: number; doubles: number };
  teenRule: string;
  /** The under-15 hours bind every under-15, so seating teens behind an adult does not help. */
  everyone: boolean;
  onSeatTeens: () => void;
  onEditCrew: () => void;
  onClose: () => void;
};

/**
 * Opens when the customer taps a day or session that does not fit the crew. It says why in one line and offers the fix
 * right there (seat the teens behind an adult and keep this choice, change the crew, or pick another), so nobody has
 * to work out the rule or walk back through the steps.
 */
export function FixSheet({ fix, passengers, need, teenRule, everyone, onSeatTeens, onEditCrew, onClose }: FixSheetProps) {
  const firstButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    firstButton.current?.focus();
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const teen = fix.reason !== "capacity";
  const who = everyone ? "افراد زیر ۱۵ سال" : "نوجوان‌ها";
  const title =
    fix.reason === "teen-day"
      ? `${who} ${fix.label} نمی‌توانند ${everyone ? "سوار شوند" : "رانندگی کنند"}`
      : fix.reason === "teen-time"
        ? `سانس ${fix.label} خارج از ساعت ${everyone ? "حضور زیر ۱۵ سال" : "رانندگی نوجوان‌ها"} است`
        : `سانس ${fix.label} برای کل گروه جا ندارد`;
  const why = teen
    ? teenRule
    : `این سانس ${fa(fix.singlesLeft)} تک‌نفره و ${fa(fix.doublesLeft)} دونفره خالی دارد و گروه شما ${karts(need.singles, need.doubles)} لازم دارد.`;

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center" role="dialog" aria-modal="true" aria-labelledby="fix-title">
      <button type="button" aria-label="بستن" onClick={onClose} className="absolute inset-0 bg-black/60 backdrop-blur-sm" tabIndex={-1} />
      <div className="carbon wizard-step relative w-full min-w-0 max-w-lg rounded-t-[2rem] border border-white/10 p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] shadow-[0_-30px_60px_-20px_rgb(0_0_0/0.9)] sm:rounded-[2rem] sm:p-6">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <span className="start-lamp lamp-static mt-1.5 shrink-0" aria-hidden="true" />
            <h3 id="fix-title" className="text-lg font-black leading-8">
              {title}
            </h3>
          </div>
          <button type="button" onClick={onClose} aria-label="بستن" className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-white/15">
            <CloseIcon className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-3 text-sm leading-7 text-on-carbon-muted">{why}</p>

        <div className="mt-5 space-y-2.5">
          {teen && passengers?.ok && (
            <button ref={firstButton} type="button" onClick={onSeatTeens} className={buttonClasses("primary", "lg", "w-full !h-auto min-h-14 flex-col !gap-0.5 !whitespace-normal px-5 py-2.5 text-center !text-base")}>
              <span>نوجوان‌ها پشت بزرگسال بنشینند؛ همین را بگیر</span>
              <span className="text-xs font-bold opacity-75">
                {karts(passengers.singles, passengers.doubles)}
                {passengers.price > 0 ? ` · ${toman(passengers.price)}` : ""}
              </span>
            </button>
          )}
          {teen && passengers && !passengers.ok && (
            <p className="rounded-2xl border border-white/10 bg-white/[0.04] p-3 text-sm leading-7 text-on-carbon-muted">
              برای نشستن نوجوان‌ها پشت بزرگسال، برای هر نوجوان یک راننده‌ی ۱۸+ با گواهینامه لازم است؛{" "}
              {passengers.missingDrivers === 1 ? "یک نفر" : `${fa(passengers.missingDrivers)} نفر`} کم دارید.
            </p>
          )}
          <button
            ref={teen && passengers?.ok ? undefined : firstButton}
            type="button"
            onClick={onEditCrew}
            className={buttonClasses(teen && passengers?.ok ? "ghost-light" : "primary", "md", "w-full")}
          >
            ویرایش خدمه
          </button>
          <button type="button" onClick={onClose} className="block w-full py-2 text-center text-sm font-bold text-on-carbon-muted underline underline-offset-4 hover:text-on-carbon">
            {fix.reason === "teen-day" ? "روز دیگری انتخاب می‌کنم" : "سانس دیگری انتخاب می‌کنم"}
          </button>
        </div>
      </div>
    </div>
  );
}
