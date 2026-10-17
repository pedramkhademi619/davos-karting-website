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

/** Days on which 11-14 year olds may drive (weekday names as the API writes them). */
export const TEEN_DAYS = new Set(["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه"]);

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

/** Sessions 11-14 year olds may drive in: starting from 15:00 to before 18:00. */
export function teenSession(time: string): boolean {
  const minutes = sessionMinutes(time);
  return minutes >= 15 * 60 && minutes < 18 * 60;
}
