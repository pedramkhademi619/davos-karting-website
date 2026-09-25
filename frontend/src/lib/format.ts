import type { PaymentStatusValue, ReservationStatus } from "@/lib/types";

const PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹";

/** "12:30" -> "۱۲:۳۰"; any Latin digit becomes a Persian one. */
export function fa(value: string | number): string {
  return String(value).replace(/[0-9]/g, (d) => PERSIAN_DIGITS[Number(d)]);
}

/** Persian or Arabic digits -> Latin, for inputs (mobile numbers, codes). */
export function toLatinDigits(value: string): string {
  return value.replace(/[۰-۹]/g, (d) => String(PERSIAN_DIGITS.indexOf(d))).replace(/[٠-٩]/g, (d) => String(d.charCodeAt(0) - 0x0660));
}

/** 790000 -> "۷۹۰٬۰۰۰" */
export function number(value: number): string {
  return fa(Math.round(value).toLocaleString("en-US")).replace(/,/g, "٬");
}

/** 790000 -> "۷۹۰٬۰۰۰ تومان" */
export function toman(value: number): string {
  return `${number(value)} تومان`;
}

/** 790000 -> "۷۹۰ هزار تومان", 1200000 -> "۱ میلیون و ۲۰۰ هزار تومان": how prices are said in Persian. */
export function tomanWords(value: number): string {
  const millions = Math.floor(value / 1_000_000);
  const thousands = Math.floor((value % 1_000_000) / 1000);
  const units = value % 1000;
  const parts: string[] = [];
  if (millions) parts.push(`${fa(millions)} میلیون`);
  if (thousands) parts.push(`${fa(thousands)} هزار`);
  if (units || parts.length === 0) parts.push(fa(units));
  return `${parts.join(" و ")} تومان`;
}

/** "2026-09-26" (Jalali numeric from the API, e.g. "1405/07/04") -> "۱۴۰۵/۰۷/۰۴" */
export function jalali(value: string): string {
  return fa(value.replaceAll("-", "/"));
}

const TEHRAN = "Asia/Tehran";

/** An ISO instant shown as Tehran wall-clock time, e.g. "۱۸:۴۵". */
export function clock(iso: string): string {
  return fa(
    new Intl.DateTimeFormat("en-GB", { timeZone: TEHRAN, hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(iso)),
  );
}

/** An ISO instant as a Jalali date and time in Tehran, e.g. "۴ مهر ۱۴۰۵، ۱۸:۴۵". */
export function dateTime(iso: string): string {
  const date = new Date(iso);
  const day = new Intl.DateTimeFormat("fa-IR-u-ca-persian", { timeZone: TEHRAN, day: "numeric", month: "long", year: "numeric" }).format(date);
  return `${day}، ${clock(iso)}`;
}

/** A calendar date ("2026-09-26") as its Jalali day and month name, e.g. { day: "۴", month: "مهر" }. */
export function jalaliParts(isoDate: string): { day: string; month: string } {
  const noon = new Date(`${isoDate}T12:00:00Z`); // noon UTC is the same calendar day in Tehran
  const parts = new Intl.DateTimeFormat("fa-IR-u-ca-persian", { timeZone: TEHRAN, day: "numeric", month: "long" }).formatToParts(noon);
  return {
    day: parts.find((p) => p.type === "day")?.value ?? "",
    month: parts.find((p) => p.type === "month")?.value ?? "",
  };
}

/** "09123456789" -> "۰۹۱۲ ۳۴۵ ۶۷۸۹" */
export function mobile(value: string): string {
  const digits = toLatinDigits(value).replace(/\D/g, "");
  if (digits.length !== 11) return fa(value);
  return fa(`${digits.slice(0, 4)} ${digits.slice(4, 7)} ${digits.slice(7)}`);
}

export const RESERVATION_STATUS: Record<ReservationStatus, { label: string; tone: "go" | "wait" | "muted" | "stop" }> = {
  held: { label: "در انتظار پرداخت", tone: "wait" },
  confirmed: { label: "قطعی", tone: "go" },
  attended: { label: "حاضر شد", tone: "muted" },
  cancelled: { label: "لغو شده", tone: "stop" },
  expired: { label: "منقضی (پرداخت نشد)", tone: "muted" },
};

export const PAYMENT_STATUS: Record<PaymentStatusValue, string> = {
  created: "ایجاد شده",
  redirected: "در درگاه بانک",
  verifying: "در حال تایید",
  unknown: "نامشخص (در حال پیگیری)",
  paid: "پرداخت شده",
  failed: "ناموفق",
  expired: "منقضی",
  refund_pending: "در انتظار بازگشت وجه",
  reversed: "وجه بازگشت داده شد",
};

export const SMS_STATUS: Record<string, string> = {
  queued: "در صف",
  sent: "ارسال شده",
  delivered: "تحویل شده",
  failed: "ناموفق",
  blocked: "مسدود توسط گیرنده",
  unknown: "نامشخص",
};

/** Karts in plain words: "۲ تک‌نفره و ۱ دونفره". */
export function karts(singles: number, doubles: number): string {
  const parts: string[] = [];
  if (singles) parts.push(`${fa(singles)} تک‌نفره`);
  if (doubles) parts.push(`${fa(doubles)} دونفره`);
  return parts.join(" و ") || "—";
}
