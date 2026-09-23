/**
 * Everything the pages say about the business lives here, so it can be replaced in one place (and later be fed by the CMS).
 *
 * Phone, working hours, the booking rule and the FAQ come from the owner (September 2026). Not published on purpose:
 * prices (the owner removed the packages from the site), a street address and an e-mail (never confirmed; the map link
 * uses the owner's own coordinates). The chat assistant reads the same facts from backend/knowledge, so change both together.
 */

export const site = {
  name: "داوس کارتینگ",
  nameLatin: "Davos Karting",
  description: "کارتینگ داوس؛ تجربه‌ای مهیج و دقیق از رانندگی و رقابت روی پیست. برای رزرو نوبت تلفنی با ما تماس بگیرید.",
  // Not used while booking is by phone. Kept because the API shares the same address (BOOKING_BASE_URL) for a future online
  // booking. `||` on purpose: an unset Docker build arg arrives as an empty string.
  bookingUrl: process.env.NEXT_PUBLIC_BOOKING_URL || "https://booking.davoskarting.ir",
  contact: {
    phone: { display: "0917 733 4894", href: "tel:09177334894" },
    hours: ["شنبه تا چهارشنبه: ۱۵ تا ۲۴", "پنجشنبه، جمعه و روزهای تعطیل: ۱۵ تا ۱ بامداد فردا"],
    map: { label: "مشاهده روی نقشه", href: "https://www.google.com/maps?q=29.76912,52.49991" },
  },
  booking: {
    short: "رزرو تلفنی",
    callToAction: "تماس برای رزرو",
    rule: "رزرو تلفنی است و هر روز برای روز بعد انجام می‌شود؛ رزرو برای همان روز ممکن نیست و برای پنجشنبه و جمعه رزرو نداریم.",
  },
} as const;

export const navigation = [
  { href: "/", label: "خانه" },
  { href: "/faq", label: "سوالات متداول" },
  { href: "/contact", label: "تماس با ما" },
] as const;

export const marqueeWords = ["سرعت", "دقت", "رقابت", "هیجان"] as const;

export const experience = [
  {
    index: "۰۱",
    icon: "bolt",
    title: "سرعت",
    text: "هیجان واقعی رانندگی؛ شتاب در مسیرهای مستقیم و کنترل در پیچ‌ها. هر دور حسی تازه دارد.",
  },
  {
    index: "۰۲",
    icon: "target",
    title: "دقت",
    text: "کارتینگ فقط فشار دادن پدال گاز نیست؛ انتخاب مسیر، ترمز به‌موقع و تمرکز است. دقیق‌تر برانید، سریع‌تر می‌شوید.",
  },
  {
    index: "۰۳",
    icon: "flag",
    title: "رقابت",
    text: "با دوستان، همکاران و خانواده رقابت کنید؛ هر دور فرصتی است برای بهتر شدن.",
  },
] as const;

export const club = {
  title: "باشگاه مشتریان داوس",
  text: "با عضویت در باشگاه مشتریان ما، از تخفیف‌های دائمی، هدایای تولد و امتیازات ویژه در هر بار رزرو بهره‌مند شوید.",
  benefits: ["تخفیف دائمی", "هدیه تولد", "امتیاز ویژه با هر رزرو"],
} as const;

/** The first three are shown on the home page, so the most useful ones come first. */
export const faqItems = [
  {
    question: "چطور نوبت رزرو کنم؟",
    answer:
      "رزرو فقط تلفنی است؛ با شماره ۰۹۱۷۷۳۳۴۸۹۴ تماس بگیرید. رزرو از روز قبل انجام می‌شود: هر روز برای روز بعد می‌توانید رزرو کنید و برای همان روز امکان‌پذیر نیست. برای پنجشنبه و جمعه رزرو نداریم.",
  },
  {
    question: "ساعت کاری چیست؟",
    answer: "شنبه تا چهارشنبه از ساعت ۱۵ تا ۲۴؛ پنجشنبه، جمعه و روزهای تعطیل از ساعت ۱۵ تا ۱ بامداد فردا.",
  },
  {
    question: "آیا محدودیت سنی و قد وجود دارد؟",
    answer:
      "افراد بالای ۱۵ سال بدون نیاز به تجربه رانندگی می‌توانند از خودروی تک‌نفره استفاده کنند. کودک زیر ۱۱ سال به هیچ عنوان نمی‌تواند رانندگی کند. افراد ۱۱ تا ۱۴ ساله فقط با قد بالای ۱۴۰ سانتی‌متر و فقط شنبه تا چهارشنبه از ساعت ۱۵ تا ۱۸ می‌توانند رانندگی کنند؛ پنجشنبه، جمعه یا خارج از این ساعت‌ها به هیچ عنوان امکان‌پذیر نیست. برای سن دقیقاً ۱۵ سال هنگام رزرو با مجموعه هماهنگ کنید.",
  },
  {
    question: "شرایط سوار شدن روی خودروی دونفره چیست؟",
    answer:
      "نفر جلو (راننده) حتماً باید ۱۸ سال یا بیشتر داشته باشد و گواهینامه و تجربه رانندگی داشته باشد، چون در ایران گواهینامه از ۱۸ سالگی صادر می‌شود؛ زیر ۱۸ سال به هیچ عنوان نمی‌تواند پشت خودروی دونفره بنشیند و بالای ۱۸ سال هم همین شرایط لازم است. نفر عقب باید خردسال و بین ۴ تا ۱۵ سال باشد. کسی که گواهینامه و تجربه رانندگی ندارد به هیچ عنوان نمی‌تواند پشت خودروی دونفره بنشیند؛ اگر بالای ۱۵ سال باشد می‌تواند از خودروی تک‌نفره استفاده کند. کودک ۴ تا ۱۵ ساله‌ای که خودش نمی‌تواند رانندگی کند می‌تواند روی صندلی عقب خودروی دونفره، پشت نفر جلو (مثلاً پدر یا مادرش) بنشیند، به شرط اینکه نفر جلو گواهینامه و توانایی رانندگی داشته باشد؛ کودک زیر ۴ سال نمی‌تواند سوار شود. استثنا: اگر هر دو نفر خانم و سبک‌وزن باشند و مجموع وزنشان زیر ۱۳۰ کیلوگرم باشد، می‌توان استثنا قائل شد؛ اما باز هم نفر جلو باید ۱۸ سال یا بیشتر داشته باشد و گواهینامه و توانایی رانندگی داشته باشد.",
  },
  {
    question: "هر سانس چند نفر ظرفیت دارد؟",
    answer: "۶ خودروی تک‌نفره و ۱ خودروی دونفره داریم؛ در هر سانس در مجموع ۸ نفر می‌توانند سوار شوند.",
  },
  {
    question: "چرا خودروی دونفره شرایط سخت‌تری دارد؟",
    answer:
      "کنترل خودروی دونفره سخت‌تر است؛ فرمانش سفت‌تر، موتورش قدرتمندتر و بدنه‌اش بلندتر است. همچنین قدرت بدنی بیشتری لازم است، چون کارتینگ کمک‌فنر ندارد و فشار زیادی به بدن وارد می‌شود؛ کودک زیر ۱۵ سال یا کسی که توانایی بدنی ندارد زود خسته می‌شود.",
  },
] as const;

/** Quick questions offered in the chat. They should match published files in backend/knowledge, or the bot will decline them. */
export const assistantSuggestions = [
  "چطور نوبت رزرو کنم؟",
  "ساعت کاری چیست؟",
  "شرایط سوار شدن روی خودروی دونفره چیست؟",
] as const;
