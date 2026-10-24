import { BOOKING_HOME, GAME_URL } from "@/lib/urls";
import { venue } from "@/lib/venue";

/**
 * Everything the pages say about the business lives here, so it can be replaced in one place.
 *
 * The working hours and the riding rules come from the owner (September 2026) and match backend/knowledge. The phone
 * number and the map location differ per deployment and come from .env (lib/venue.ts). Numbers the owner changes in the
 * admin panel (prices, karts per session, days without booking, hold time) are NOT written here: pages read them from
 * the API (/api/v1/reservations/info), see content/faq.ts. The street address (October 2026) is in the
 * structured data; no e-mail is published.
 */

/** Opening hours, written once: the pages show `label: text`, search engines get the schema.org days and times. */
const openingHours = [
  {
    label: "شنبه تا چهارشنبه",
    text: "۱۵ تا ۲۴",
    schemaDays: ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday"],
    opens: "15:00",
    closes: "24:00",
  },
  {
    label: "پنجشنبه، جمعه و روزهای تعطیل",
    text: "۱۵ تا ۱ بامداد فردا",
    schemaDays: ["Thursday", "Friday"],
    opens: "15:00",
    closes: "01:00",
  },
] as const;

export const site = {
  name: "داووس کارتینگ",
  nameLatin: "Davos Karting",
  city: "شیراز",
  region: "فارس",
  /** The track's street address as the owner gave it (October 2026); used in the structured data. */
  streetAddress: "آرش ۱، جاده شیراز-صدرا، بلوار مهرگان، جوانمردی (شهرک بهاران)",
  /** Official social profiles (schema.org sameAs). Add a page here only once it really exists. */
  sameAs: [] as string[],
  description:
    "کارتینگ شیراز؛ پیست کارتینگ حرفه‌ای داووس با خودروهای تک‌نفره و دونفره. جای خالی سانس‌ها را آنلاین ببینید، قیمت و شرایط سنی را بدانید و رزرو کنید.",
  contact: {
    phone: venue.phone,
    openingHours,
    map: { label: "مسیریابی روی نقشه", href: venue.mapHref },
    /** The owner's pin on Neshan (the map most people in Iran route with). */
    neshan: { label: "مسیریابی با نشان", href: "https://nshn.ir/b6_bgmLANFsp7u" },
    geo: venue.geo,
  },
  booking: {
    href: BOOKING_HOME, // the booking subdomain when there is one (lib/urls.ts)
    short: "رزرو آنلاین",
    callToAction: "رزرو آنلاین سانس",
    phoneCallToAction: "رزرو تلفنی",
  },
} as const;

/** The owner's arrival rule (October 2026), shown on every ticket and in the FAQ. */
export const arrivalRule =
  "ده دقیقه قبل از شروع سانس توی سالن باشید. اگه دیر برسید و سانس‌تون شروع شده باشه، دیگه نمی‌تونیم سوارتون کنیم؛ نوبت‌تون می‌سوزه و پولش هم برنمی‌گرده.";

export const navigation = [
  { href: "/", label: "خانه" },
  { href: "/track", label: "پیست" },
  { href: "/rules", label: "شرایط سوار شدن" },
  { href: "/booking", label: "رزرو سانس" },
  ...(GAME_URL ? [{ href: GAME_URL, label: "بازی" }] : []),
  { href: "/faq", label: "سوالات متداول" },
  { href: "/contact", label: "تماس با ما" },
] as const;

export const marqueeWords = ["سرعت", "دقت", "رقابت", "هیجان", "آدرنالین", "خط پایان"] as const;

/** How online booking works, shown on the home page (the steps of the booking wizard, components/booking/wizard). */
export const bookingSteps = [
  { title: "چند نفرید؟", text: "تعداد و سن نفرات رو وارد کنید؛ سایت ماشین‌ها رو خودش می‌چینه." },
  { title: "روز و ساعت", text: "یه سانس خالی انتخاب کنید." },
  { title: "ثبت و پرداخت", text: "رزرو رو ثبت کنید و آنلاین پرداخت کنید." },
  { title: "بلیت", text: "شماره بلیت توی «حساب من» هست. ده دقیقه قبل از سانس توی پیست باشید." },
] as const;

/** Owner's riding rules (not admin settings), summarised for the home page. Kept identical to backend/knowledge. */
export const ridingRules = [
  { badge: "15+", title: "تک‌نفره برای همه", text: "از ۱۵ سال به بالا، حتی اگه تا حالا رانندگی نکردید؛ شرط قد و ساعت هم نداره." },
  {
    badge: "11–14",
    title: "نوجوون‌ها با شرط",
    text: "فقط با قد بالای ۱۴۰ سانت و فقط شنبه تا چهارشنبه، ساعت ۱۵ تا ۱۸.",
  },
  { badge: "18+", title: "راننده‌ی دونفره", text: "۱۸ سال به بالا، با گواهینامه و دست‌فرمون خوب؛ پشت سرش یه بچه‌ی ۴ تا ۱۴ ساله می‌شینه." },
  { badge: "4–10", title: "کوچولوها", text: "زیر ۱۱ سال رانندگی نمی‌کنن، ولی از ۴ سالگی می‌تونن صندلی عقب دونفره، پشت مامان یا باباشون بشینن." },
] as const;

/** Quick questions offered in the chat. They should match published files in backend/knowledge, or the bot will decline them. */
export const assistantSuggestions = [
  "چطور آنلاین رزرو کنم؟",
  "پسرم ۱۲ سالشه، می‌تونه تک‌نفره برونه؟",
  "۹ نفریم، چند سانس لازمه؟",
] as const;
