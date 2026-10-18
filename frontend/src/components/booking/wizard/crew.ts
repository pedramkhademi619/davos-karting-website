/**
 * The crew step's rules: who is coming decides which karts are needed. These are the owner's riding rules (see
 * content/site.ts ridingRules and backend/knowledge), turned into a kart mix so the customer never has to work out
 * "single or double" alone:
 *
 * - licensed: 18+ with a driving licence. Drives a single, or a double with a child behind.
 * - adult: 16+ without a licence (or 16-17). Single only.
 * - teen: 11-14 and taller than 140 cm. Single, but only Saturday to Wednesday in sessions starting 15:00-17:59;
 *   otherwise rides behind a licensed adult.
 * - kid: 4-15 who cannot drive (under 11, 15 years old, or a teen under 140 cm). Back seat of a double only.
 */
export type Crew = { licensed: number; adult: number; teen: number; kid: number };

export const EMPTY_CREW: Crew = { licensed: 1, adult: 0, teen: 0, kid: 0 };

/**
 * When under-15s may ride, from the admin panel (BookingInfo.junior_*): weekday names as the API writes them, sessions
 * starting from `from` up to before `until`. `everyone` binds back-seat passengers too; otherwise only 11-14 year olds
 * who drive a single-seater.
 */
export type JuniorWindow = { days: ReadonlySet<string>; from: string; until: string; everyone: boolean };

/** The owner's rule, used until the settings have loaded: Saturday to Wednesday, 15:00 to 18:00, young drivers only. */
export const DEFAULT_JUNIOR_WINDOW: JuniorWindow = {
  days: new Set(["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه"]),
  from: "15:00",
  until: "18:00",
  everyone: false,
};

/** "شنبه تا چهارشنبه" for that run of days, otherwise the names one by one. */
const WEEK = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"];
export function dayRange(days: ReadonlySet<string>): string {
  const ordered = WEEK.filter((d) => days.has(d));
  const start = WEEK.indexOf(ordered[0]);
  const contiguous = ordered.length >= 3 && ordered.every((d, i) => WEEK[start + i] === d);
  return contiguous ? `${ordered[0]} تا ${ordered[ordered.length - 1]}` : ordered.join("، ");
}

/** The rule in one sentence for the fix sheet. */
export function juniorRule(window: JuniorWindow, fa: (v: string) => string): string {
  const when = `${dayRange(window.days)} و در سانس‌های ساعت ${fa(window.from)} تا ${fa(window.until)}`;
  return window.everyone
    ? `افراد زیر ۱۵ سال (چه راننده و چه سرنشین صندلی عقب) فقط ${when} می‌توانند سوار شوند.`
    : `رانندگی نوجوان‌های ۱۱ تا ۱۴ سال فقط ${when} مجاز است. می‌توانند پشت یک بزرگسال گواهینامه‌دار بنشینند؛ آن‌وقت همه‌ی روزها و ساعت‌ها باز است.`;
}

export type KartPlan =
  | { ok: true; singles: number; doubles: number; teenDrivers: number; people: number }
  | { ok: false; reason: string; singles: number; doubles: number; teenDrivers: number; people: number };

/**
 * Karts for a crew. `teensDrive` false puts the teens in the back seat of doubles (needed on Thursday and Friday, or in
 * evening sessions). Each passenger needs a licensed driver; licensed adults left over drive singles.
 */
export function planKarts(crew: Crew, teensDrive: boolean, maxKarts: number): KartPlan {
  const people = crew.licensed + crew.adult + crew.teen + crew.kid;
  const passengers = crew.kid + (teensDrive ? 0 : crew.teen);
  const teenDrivers = teensDrive ? crew.teen : 0;
  const doubles = passengers;
  const singles = Math.max(0, crew.licensed - passengers) + crew.adult + teenDrivers;
  const base = { singles, doubles, teenDrivers, people };
  if (people === 0) return { ok: false, reason: "حداقل یک نفر را اضافه کنید.", ...base };
  if (passengers > crew.licensed) {
    const missing = passengers - crew.licensed;
    return {
      ok: false,
      reason: `هر کودک باید پشت یک راننده‌ی ۱۸+ با گواهینامه بنشیند؛ ${missing === 1 ? "یک" : missing.toLocaleString("fa-IR")} راننده‌ی گواهینامه‌دار کم است.`,
      ...base,
    };
  }
  if (singles + doubles > maxKarts) {
    return {
      ok: false,
      reason: `در هر رزرو آنلاین حداکثر ${maxKarts.toLocaleString("fa-IR")} خودرو؛ گروه را در دو رزرو جدا ثبت کنید یا تماس بگیرید.`,
      ...base,
    };
  }
  return { ok: true, ...base };
}

/** Minutes since the business day's start; times after midnight (00:15 ... 05:59) belong to the same evening. */
export function sessionMinutes(time: string): number {
  const [h, m] = time.split(":").map(Number);
  const value = h * 60 + m;
  return h < 6 ? value + 24 * 60 : value;
}

/** A session start inside the under-15 hours. */
export function juniorSession(time: string, window: JuniorWindow): boolean {
  const minutes = sessionMinutes(time);
  return minutes >= sessionMinutes(window.from) && minutes < sessionMinutes(window.until);
}
