import { ridingRules, site } from "@/content/site";
import { fa } from "@/lib/format";
import type { BookingInfo } from "@/lib/types";

export type HoursLine = { label: string; text: string };

/** "10:00" → "۱۰", "10:30" → "۱۰:۳۰": on-the-hour times read like the owner's evening hours ("۱۵ تا ۲۴"). */
function hour(value: string): string {
  return fa(value.endsWith(":00") ? String(Number(value.slice(0, -3))) : value);
}

/**
 * The opening hours as lines: the morning shift from the admin panel (when there is one), then the owner's evening
 * hours from content/site.ts. Without the settings (API unreachable) only the evening hours are shown.
 */
export function openingLines(info: BookingInfo | null): HoursLine[] {
  const evening = site.contact.openingHours.map(({ label, text }) => ({ label, text }));
  if (!info?.morning_shift_enabled) return evening;
  return [
    { label: "شیفت صبح، همه‌ی روزها", text: `${hour(info.morning_first_session)} تا ${hour(info.morning_last_session_before)}` },
    ...evening.map((line) => ({ label: `شیفت عصر، ${line.label}`, text: line.text })),
  ];
}

/** "شنبه تا چهارشنبه" for a run of the week, otherwise the names joined with "، ". */
export function weekdayRange(names: readonly string[]): string {
  const week = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"];
  const ordered = week.filter((d) => names.includes(d));
  if (ordered.length === 0) return "";
  const start = week.indexOf(ordered[0]);
  const contiguous = ordered.length >= 3 && ordered.every((d, i) => week[start + i] === d);
  return contiguous ? `${ordered[0]} تا ${ordered[ordered.length - 1]}` : ordered.join("، ");
}

/** The under-15 hours in words ("شنبه تا چهارشنبه از ساعت ۱۵:۰۰ تا ۱۸:۰۰"); null without the settings. */
export function juniorHours(info: BookingInfo | null): string | null {
  if (!info) return null;
  return `${weekdayRange(info.junior_weekdays)} از ساعت ${fa(info.junior_from)} تا ${fa(info.junior_until)}`;
}

/** The owner's riding rules with the under-15 days and hours from the admin panel (content/site.ts holds the defaults). */
export function ridingRulesFor(info: BookingInfo | null): { badge: string; title: string; text: string }[] {
  const hours = juniorHours(info);
  return ridingRules.map((rule) => {
    if (!hours) return { ...rule };
    if (rule.badge === "11–14") return { ...rule, text: `فقط با قد بالای ۱۴۰ سانت و فقط ${hours}.` };
    if (rule.badge === "4–10" && info?.junior_scope === "everyone") return { ...rule, text: `${rule.text} زیر ۱۵ سال‌ها فقط ${hours} می‌تونن بیان.` };
    return { ...rule };
  });
}
