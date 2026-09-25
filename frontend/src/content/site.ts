import { BOOKING_HOME } from "@/lib/urls";

/**
 * Everything the pages say about the business lives here, so it can be replaced in one place.
 *
 * Phone, working hours and the riding rules come from the owner (September 2026) and match backend/knowledge. Numbers the
 * owner changes in the admin panel (prices, karts per session, days without booking, hold time) are NOT written here: pages
 * read them from the API (/api/v1/reservations/info), see content/faq.ts. No street address or e-mail is published because
 * none was confirmed; the map link uses the owner's own coordinates.
 */

export const site = {
  name: "داوس کارتینگ",
  nameLatin: "Davos Karting",
  description:
    "کارتینگ داوس؛ پیست حرفه‌ای با خودروهای تک‌نفره و دونفره. سانس دلخواه را آنلاین ببینید، رزرو کنید و از درگاه بانک ملت پرداخت کنید.",
  contact: {
    phone: { display: "0917 733 4894", href: "tel:09177334894", e164: "+989177334894" },
    hours: ["شنبه تا چهارشنبه: ۱۵ تا ۲۴", "پنجشنبه، جمعه و روزهای تعطیل: ۱۵ تا ۱ بامداد فردا"],
    map: { label: "مسیریابی روی نقشه", href: "https://www.google.com/maps?q=29.76912,52.49991" },
    geo: { latitude: 29.76912, longitude: 52.49991 },
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
  { href: "/booking", label: "رزرو سانس" },
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

/** How online booking works, shown on the home page. */
export const bookingSteps = [
  { title: "ورود با موبایل", text: "شماره موبایل را بزنید و با کد پیامکی وارد شوید؛ بدون رمز عبور." },
  { title: "انتخاب سانس", text: "روز و ساعت دلخواه را ببینید؛ جای خالی هر سانس زنده نمایش داده می‌شود." },
  { title: "پرداخت امن", text: "تعداد خودرو را انتخاب کنید و مبلغ را از درگاه رسمی بانک ملت بپردازید." },
  { title: "بلیت پیامکی", text: "کد رزرو پیامک می‌شود و در «حساب من» هم هست؛ همان را در پیست نشان دهید." },
] as const;

/** Owner's riding rules (not admin settings), summarised for the home page. Kept identical to backend/knowledge. */
export const ridingRules = [
  { badge: "16+", title: "تک‌نفره برای همه", text: "از ۱۶ سال به بالا، حتی بدون تجربه رانندگی، بدون شرط قد یا ساعت." },
  {
    badge: "11–14",
    title: "نوجوان‌ها با شرط",
    text: "فقط با قد بیشتر از ۱۴۰ سانتی‌متر و فقط شنبه تا چهارشنبه از ساعت ۱۵ تا ۱۸.",
  },
  { badge: "18+", title: "راننده دونفره", text: "۱۸ سال به بالا با گواهینامه و توانایی رانندگی؛ پشت سرش کودک ۴ تا ۱۵ ساله." },
  { badge: "4–10", title: "کوچولوها", text: "کودک زیر ۱۱ سال رانندگی نمی‌کند، ولی از ۴ سالگی روی صندلی عقب دونفره، پشت پدر یا مادرش، هیجان را حس می‌کند." },
] as const;

/** Quick questions offered in the chat. They should match published files in backend/knowledge, or the bot will decline them. */
export const assistantSuggestions = [
  "چطور آنلاین رزرو کنم؟",
  "پسرم ۱۲ سالشه، می‌تونه تک‌نفره برونه؟",
  "۹ نفریم، چند سانس لازمه؟",
] as const;
