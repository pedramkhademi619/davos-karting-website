import { arrivalRule, site } from "@/content/site";
import { fa, tomanWords } from "@/lib/format";
import { juniorHours, openingLines } from "@/lib/hours";
import type { BookingInfo } from "@/lib/types";

export type FaqItem = { readonly question: string; readonly answer: string };

function days(names: readonly string[]): string {
  if (names.length === 0) return "";
  if (names.length === 1) return names[0];
  return `${names.slice(0, -1).join("، ")} و ${names[names.length - 1]}`;
}

/**
 * The FAQ. Answers that depend on the admin panel's settings (prices, karts per session, booking days, hold time) are built
 * from them, so the site never contradicts the booking page or the assistant. Without the settings (API unreachable) those
 * answers fall back to wording without numbers.
 */
export function buildFaq(info: BookingInfo | null): FaqItem[] {
  const phone = site.contact.phone ? `رزرو تلفنی هم با ${fa(site.contact.phone.local)} انجام میشه.` : "";
  const hours = openingLines(info).map(({ label, text }) => `${label} از ساعت ${text}`).join("؛ ");
  const junior = juniorHours(info) ?? "شنبه تا چهارشنبه از ساعت ۱۵ تا ۱۸";
  const closed = info ? days(info.closed_weekdays) : "";
  const booking = info
    ? `توی صفحه‌ی «رزرو سانس» بگید با چند نفر میاید تا ماشین‌ها چیده بشن، روز و سانس رو از روی جدول انتخاب کنید، با شماره موبایل وارد بشید و رزرو رو ثبت کنید. ماشین‌ها ${fa(
        info.hold_minutes,
      )} دقیقه براتون نگه داشته میشن تا پرداخت کنید؛ شماره بلیتتون رو هم توی صفحه‌ی «حساب من» می‌بینید. ${
        info.min_days_ahead === 0 ? "برای همون روز هم میشه رزرو کرد." : "رزرو از روز قبل انجام میشه و برای همون روز نمیشه."
      }${closed ? ` ${closed} رزرو نداریم.` : ""} ${phone}`
    : `از صفحه‌ی «رزرو سانس» با شماره موبایل وارد بشید، یه سانس خالی انتخاب کنید و رزرو رو ثبت کنید؛ شماره بلیتتون رو توی صفحه‌ی «حساب من» می‌بینید. ${phone}`;

  const items: FaqItem[] = [
    {
      question: "کارتینگ داووس توی شیراز کجاست؟",
      answer: `پیست کارتینگ داووس توی ${site.city}ه: ${site.streetAddress}. موقعیت دقیق رو از «مسیریابی روی نقشه» یا «مسیریابی با نشان» توی صفحه‌ی تماس ببینید.`,
    },
    { question: "چطوری کارتینگ رو آنلاین رزرو کنم؟", answer: booking },
    {
      question: "ساعت کاری‌تون چیه؟",
      answer: `${hours}.`,
    },
    {
      question: "محدودیت سنی و قد دارید؟",
      answer:
        `از ۱۵ سال به بالا (خود ۱۵ ساله هم) می‌تونید با ماشین تک‌نفره برونید، حتی اگه تا حالا رانندگی نکردید؛ شرط قد، روز یا ساعت هم نداره. بچه‌های زیر ۱۱ سال اصلاً رانندگی نمی‌کنن. نوجوون‌های ۱۱ تا ۱۴ ساله فقط با قد بالای ۱۴۰ سانت و فقط ${junior} می‌تونن برونن.${info?.junior_scope === "everyone" ? ` همه‌ی زیر ۱۵ سال‌ها (حتی روی صندلی عقب) فقط ${junior} می‌تونن بیان.` : ""}`,
    },
    {
      question: "کلاه ایمنی باید خودمون بیاریم؟",
      answer: "نه، لازم نیست. قبل از سوار شدن، کلاه ایمنی و کلاه بهداشتی رو خودمون بهتون می‌دیم.",
    },
    {
      question: "شرایط سوار شدن ماشین دونفره چیه؟",
      answer:
        "راننده (نفر جلو) باید ۱۸ سال یا بیشتر داشته باشه، گواهینامه داشته باشه و رانندگی بلد باشه؛ نفر عقب باید یه بچه‌ی ۴ تا ۱۴ ساله باشه. بچه‌ای که خودش نمی‌تونه برونه، صندلی عقب پشت مامان یا باباش می‌شینه؛ زیر ۴ سال اصلاً سوار نمیشه. دو تا بزرگسال با هم سوار دونفره نمیشن، مگه دو تا خانم سبک‌وزن که جمع وزنشون زیر ۱۳۰ کیلو باشه و نفر جلو شرایط راننده رو داشته باشه.",
    },
  ];

  if (info) {
    items.push(
      {
        question: "هر سانس چند نفر جا داره؟",
        answer: `هر سانس ${fa(info.single_capacity)} تا ماشین تک‌نفره و ${fa(
          info.double_capacity,
        )} تا دونفره داریم. هر بزرگسال با یه تک‌نفره میره؛ اگه پشت راننده‌ی هر دونفره یه بچه‌ی ۴ تا ۱۴ ساله بشینه، جای سانس به ${fa(
          info.single_capacity + 2 * info.double_capacity,
        )} نفر می‌رسه.`,
      },
      {
        question: "قیمت کارتینگ داووس چنده؟",
        answer: `روزهای عادی: تک‌نفره ${tomanWords(info.normal_single_toman)} و دونفره ${tomanWords(
          info.normal_double_toman,
        )}. روزهای تعطیل${info.holiday_weekdays.length ? ` (${days(info.holiday_weekdays)} و تعطیلات رسمی)` : ""}: تک‌نفره ${tomanWords(
          info.holiday_single_toman,
        )} و دونفره ${tomanWords(info.holiday_double_toman)}. قیمت‌ها برای هر ماشین و یه سانسه.`,
      },
    );
  }

  items.push(
    {
      question: "اگه دیر برسم چی میشه؟",
      answer: arrivalRule,
    },
    {
      question: "اگه بارون بیاد یا هوا بد بشه چی میشه؟",
      answer:
        "پیست روبازه و با بارون یا هوای بد تعطیل میشه. اون موقع پول برنمی‌گرده و رزروتون به یه روز و سانس دیگه منتقل میشه؛ پس قبل از رزرو حتماً هوا رو چک کنید.",
    },
    {
      question: "اگه پول کم شد ولی رزرو ثبت نشد چی؟",
      answer:
        "نگران نباشید؛ پرداخت‌ها با بانک چک میشن. اگه پول از حسابتون کم شده ولی رزرو قطعی نشده، بانک خودش پول رو برمی‌گردونه. وضعیت رو توی «حساب من» ببینید یا با ما تماس بگیرید.",
    },
    {
      question: "چرا ماشین دونفره شرایط سخت‌تری داره؟",
      answer:
        "چون کنترلش سخت‌تره؛ فرمونش سفت‌تره، موتورش قوی‌تره و بدنه‌ش بلندتره. کارتینگ کمک‌فنر نداره و فشار زیادی به بدن میاد، برای همین راننده باید هم زور بدنی داشته باشه هم تجربه.",
    },
  );
  return items;
}
