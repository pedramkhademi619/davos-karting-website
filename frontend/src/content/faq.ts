import { site } from "@/content/site";
import { fa, tomanWords } from "@/lib/format";
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
  const phone = `رزرو تلفنی هم با ${fa(site.contact.phone.local)} انجام می‌شود.`;
  const hours = site.contact.openingHours.map(({ label, text }) => `${label} از ساعت ${text}`).join("؛ ");
  const closed = info ? days(info.closed_weekdays) : "";
  const booking = info
    ? `از صفحه «رزرو سانس» با شماره موبایل وارد شوید، سانس خالی را انتخاب کنید و مبلغ را از درگاه بانک ملت بپردازید؛ خودروها ${fa(
        info.hold_minutes,
      )} دقیقه برای پرداخت نگه داشته می‌شوند و کد رزرو پیامک می‌شود. ${
        info.min_days_ahead === 0 ? "رزرو برای همان روز هم ممکن است." : "رزرو از روز قبل انجام می‌شود و برای همان روز ممکن نیست."
      }${closed ? ` برای ${closed} رزرو نداریم.` : ""} ${phone}`
    : `از صفحه «رزرو سانس» با شماره موبایل وارد شوید، سانس خالی را انتخاب کنید و مبلغ را از درگاه بانک ملت بپردازید؛ کد رزرو پیامک می‌شود. ${phone}`;

  const items: FaqItem[] = [
    { question: "چطور نوبت رزرو کنم؟", answer: booking },
    {
      question: "ساعت کاری چیست؟",
      answer: `${hours}.`,
    },
    {
      question: "آیا محدودیت سنی و قد وجود دارد؟",
      answer:
        "از ۱۶ سال به بالا بدون نیاز به تجربه رانندگی می‌توانید با خودروی تک‌نفره برانید. کودک زیر ۱۱ سال به هیچ عنوان رانندگی نمی‌کند. افراد ۱۱ تا ۱۴ ساله فقط با قد بیشتر از ۱۴۰ سانتی‌متر و فقط شنبه تا چهارشنبه از ساعت ۱۵ تا ۱۸ می‌توانند برانند. برای سن دقیقاً ۱۵ سال هنگام رزرو با مجموعه هماهنگ کنید.",
    },
    {
      question: "شرایط سوار شدن روی خودروی دونفره چیست؟",
      answer:
        "نفر جلو (راننده) باید ۱۸ سال یا بیشتر باشد و گواهینامه و توانایی رانندگی داشته باشد؛ نفر عقب باید کودک ۴ تا ۱۵ ساله باشد. کودکی که خودش نمی‌تواند رانندگی کند روی صندلی عقب، پشت پدر یا مادرش، می‌نشیند؛ کودک زیر ۴ سال سوار نمی‌شود. دو بزرگسال با هم سوار دونفره نمی‌شوند، مگر دو خانم سبک‌وزن با مجموع وزن زیر ۱۳۰ کیلوگرم که نفر جلو شرایط راننده را داشته باشد.",
    },
  ];

  if (info) {
    items.push(
      {
        question: "هر سانس چند نفر ظرفیت دارد؟",
        answer: `در هر سانس ${fa(info.single_capacity)} خودروی تک‌نفره و ${fa(
          info.double_capacity,
        )} خودروی دونفره داریم. بزرگسالان هر کدام با یک تک‌نفره می‌روند؛ اگر پشت راننده هر دونفره یک کودک ۴ تا ۱۵ ساله بنشیند، ظرفیت سانس به ${fa(
          info.single_capacity + 2 * info.double_capacity,
        )} نفر می‌رسد.`,
      },
      {
        question: "قیمت‌ها چقدر است؟",
        answer: `روزهای عادی: تک‌نفره ${tomanWords(info.normal_single_toman)} و دونفره ${tomanWords(
          info.normal_double_toman,
        )}. روزهای تعطیل${info.holiday_weekdays.length ? ` (${days(info.holiday_weekdays)} و تعطیلات رسمی)` : ""}: تک‌نفره ${tomanWords(
          info.holiday_single_toman,
        )} و دونفره ${tomanWords(info.holiday_double_toman)}. قیمت هر خودرو برای یک سانس است.`,
      },
    );
  }

  items.push(
    {
      question: "اگر پرداخت انجام شد ولی رزرو ثبت نشد چه می‌شود؟",
      answer:
        "پرداخت‌ها با بانک تطبیق داده می‌شوند. اگر مبلغ از حسابتان کم شده ولی به هر دلیل رزرو قطعی نشد، مبلغ به‌طور خودکار از طرف بانک برگشت داده می‌شود؛ وضعیت را در «حساب من» ببینید یا با ما تماس بگیرید.",
    },
    {
      question: "چرا خودروی دونفره شرایط سخت‌تری دارد؟",
      answer:
        "کنترل خودروی دونفره سخت‌تر است؛ فرمانش سفت‌تر، موتورش قدرتمندتر و بدنه‌اش بلندتر است. کارتینگ کمک‌فنر ندارد و فشار زیادی به بدن وارد می‌شود، پس راننده باید قدرت بدنی و تجربه کافی داشته باشد.",
    },
  );
  return items;
}
