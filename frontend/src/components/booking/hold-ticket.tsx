"use client";

import { buttonClasses } from "@/components/button-link";
import { useCountdown } from "@/components/booking/use-countdown";
import { ShieldIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { fa, jalali, karts, toman } from "@/lib/format";
import type { Reservation } from "@/lib/types";

type HoldTicketProps = {
  reservation: Reservation;
  holdMinutes: number;
  paying: boolean;
  releasing: boolean;
  error: string | null;
  onPay: () => void;
  onRelease: () => void;
  onRestart: () => void;
};

/** The held seats as a ticket with the hold countdown; paying sends the browser to the bank. */
export function HoldTicket({ reservation, holdMinutes, paying, releasing, error, onPay, onRelease, onRestart }: HoldTicketProps) {
  const left = useCountdown(reservation.hold_expires_at);
  const expired = left !== null && left <= 0;
  const total = Math.max(1, holdMinutes * 60);
  const progress = left === null ? 1 : Math.min(1, left / total);
  const mm = left === null ? "" : `${fa(Math.floor(left / 60))}:${fa(String(left % 60).padStart(2, "0"))}`;

  return (
    <div className="pop mx-auto max-w-xl">
      <div className="ticket carbon overflow-hidden shadow-[0_40px_80px_-40px_rgb(12_13_16/0.9)]">
        <div className="relative p-7 md:p-9">
          <div className="flex items-start justify-between gap-6">
            <div>
              <p className="text-sm font-bold text-accent">خودروها برای شما نگه داشته شد</p>
              <p className="race-number mt-3 text-3xl font-black tracking-wider" dir="ltr">
                {reservation.code}
              </p>
            </div>
            <div
              className="grid h-24 w-24 shrink-0 place-items-center rounded-full"
              style={{ background: `conic-gradient(${expired ? "#d90a00" : "#ffc400"} ${progress * 360}deg, rgb(255 255 255 / 0.1) 0)` }}
              role="timer"
              aria-label={expired ? "زمان نگه‌داری تمام شد" : `زمان باقی‌مانده ${mm}`}
            >
              <span className="grid h-[5.2rem] w-[5.2rem] place-items-center rounded-full bg-carbon text-center">
                <span className="text-xl font-black leading-none" dir="ltr">
                  {expired ? "۰:۰۰" : mm}
                </span>
              </span>
            </div>
          </div>

          <dl className="mt-8 grid grid-cols-2 gap-x-6 gap-y-5">
            <div>
              <dt className="text-xs text-on-carbon-muted">روز</dt>
              <dd className="mt-1 font-black">
                {reservation.weekday} {jalali(reservation.date_jalali)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-on-carbon-muted">ساعت سانس</dt>
              <dd className="mt-1 font-black">{fa(reservation.time)}</dd>
            </div>
            <div>
              <dt className="text-xs text-on-carbon-muted">خودروها</dt>
              <dd className="mt-1 font-black">{karts(reservation.single_count, reservation.double_count)}</dd>
            </div>
            <div>
              <dt className="text-xs text-on-carbon-muted">مبلغ قابل پرداخت</dt>
              <dd className="mt-1 text-xl font-black text-accent">{toman(reservation.amount_toman)}</dd>
            </div>
          </dl>
        </div>
        <div className="checker" aria-hidden="true" />
        <div className="space-y-4 p-7 md:p-9">
          {error && <Alert tone="error">{error}</Alert>}
          {expired ? (
            <>
              <Alert tone="warning">زمان نگه‌داری خودروها تمام شد. دوباره سانس را انتخاب کنید.</Alert>
              <button type="button" onClick={onRestart} className={buttonClasses("primary", "lg", "w-full")}>
                انتخاب دوباره
              </button>
            </>
          ) : (
            <>
              <button type="button" onClick={onPay} disabled={paying || releasing} className={buttonClasses("primary", "lg", "w-full")}>
                {paying ? <Spinner label="در حال انتقال به بانک" /> : `پرداخت ${toman(reservation.amount_toman)}`}
              </button>
              <p className="flex items-center justify-center gap-2 text-center text-xs text-on-carbon-muted">
                <ShieldIcon className="h-4 w-4 text-go" />
                پرداخت در صفحه رسمی بانک ملت (شاپرک) انجام می‌شود؛ اطلاعات کارت را فقط آنجا وارد کنید.
              </p>
              <button
                type="button"
                onClick={onRelease}
                disabled={paying || releasing}
                className="mx-auto block text-sm font-bold text-on-carbon-muted underline underline-offset-4 hover:text-on-carbon"
              >
                {releasing ? "در حال آزاد کردن..." : "انصراف و آزاد کردن خودروها"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
