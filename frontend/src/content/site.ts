import { BOOKING_HOME, GAME_URL } from "@/lib/urls";
import { venue } from "@/lib/venue";

/**
 * Everything the pages say about the business lives here, so it can be replaced in one place.
 *
 * The working hours and the riding rules come from the owner (September 2026) and match backend/knowledge. The phone
 * number and the map location differ per deployment and come from .env (lib/venue.ts). Numbers the owner changes in the
 * admin panel (prices, karts per session, days without booking, hold time) are NOT written here: pages read them from
 * the API (/api/v1/reservations/info), see content/faq.ts. No street address or e-mail is published because none was
 * confirmed.
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
  description:
    "کارتینگ داووس؛ پیست حرفه‌ای با خودروهای تک‌نفره و دونفره. سانس دلخواه را آنلاین ببینید، رزرو کنید و از درگاه بانک ملت پرداخت کنید.",
  contact: {
    phone: venue.phone,
    openingHours,
    map: { label: "مسیریابی روی نقشه", href: venue.mapHref },
    geo: venue.geo,
  },
  booking: {
    href: BOOKING_HOME, // the booking subdomain when there is one (lib/urls.ts)
    short: "رزرو آنلاین",
    callToAction: "رزرو آنلاین سانس",
    phoneCallToAction: "رزرو تلفنی",
  },
} as const;

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

export const experience = [
  {
    index: "01",
    icon: "bolt",
    title: "سرعت",
    text: "شتاب در مسیرهای مستقیم و کنترل در پیچ‌ها؛ هر دور حسی تازه دارد و هر ثانیه به حساب می‌آید.",
  },
  {
    index: "02",
    icon: "target",
    title: "دقت",
    text: "کارتینگ فقط فشار دادن پدال گاز نیست؛ انتخاب مسیر، ترمز به‌موقع و تمرکز است. دقیق‌تر برانید، سریع‌تر می‌شوید.",
  },
  {
    index: "03",
    icon: "flag",
    title: "رقابت",
    text: "با دوستان، همکاران و خانواده رقابت کنید؛ هر سانس فرصتی است برای رسیدن زودتر به خط پایان.",
  },
] as const;

/** How online booking works, shown on the home page (the steps of the booking wizard, components/booking/wizard). */
export const bookingSteps = [
  { title: "خدمه را بچینید", text: "بگویید چه کسانی می‌آیند؛ خودروهای تک‌نفره و دونفره را طبق قوانین سن و قد خودمان می‌چینیم." },
  { title: "روز و سانس", text: "از روی جدول استارت انتخاب کنید؛ فقط سانس‌هایی که برای کل گروه جا دارند روشن می‌مانند." },
  { title: "لانچ کنترل", text: "دکمه را نگه دارید تا چراغ‌ها خاموش شوند؛ خودروها برایتان نگه داشته می‌شود و از درگاه بانک ملت می‌پردازید." },
  { title: "پاس پیامکی", text: "شماره بلیت پیامک می‌شود و در «حساب من» هم هست؛ همان را در پیست نشان دهید." },
] as const;

/** Owner's riding rules (not admin settings), summarised for the home page. Kept identical to backend/knowledge. */
export const ridingRules = [
  { badge: "15+", title: "تک‌نفره برای همه", text: "از ۱۵ سال به بالا، حتی بدون تجربه رانندگی، بدون شرط قد یا ساعت." },
  {
    badge: "11–14",
    title: "نوجوان‌ها با شرط",
    text: "فقط با قد بیشتر از ۱۴۰ سانتی‌متر و فقط شنبه تا چهارشنبه از ساعت ۱۵ تا ۱۸.",
  },
  { badge: "18+", title: "راننده دونفره", text: "۱۸ سال به بالا با گواهینامه و توانایی رانندگی؛ پشت سرش کودک ۴ تا ۱۴ ساله." },
  { badge: "4–10", title: "کوچولوها", text: "کودک زیر ۱۱ سال رانندگی نمی‌کند، ولی از ۴ سالگی روی صندلی عقب دونفره، پشت پدر یا مادرش، هیجان را حس می‌کند." },
] as const;

/** Quick questions offered in the chat. They should match published files in backend/knowledge, or the bot will decline them. */
export const assistantSuggestions = [
  "چطور آنلاین رزرو کنم؟",
  "پسرم ۱۲ سالشه، می‌تونه تک‌نفره برونه؟",
  "۹ نفریم، چند سانس لازمه؟",
] as const;
