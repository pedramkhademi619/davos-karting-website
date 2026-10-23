import Link from "next/link";
import { SectionHeading } from "@/components/section-heading";
import { site } from "@/content/site";

/**
 * A short, plain description of the business for people (and search engines) who arrive by searching "کارتینگ شیراز":
 * what it is, where, what to expect and where to read more. Only facts that are true for every deployment (nothing
 * from the admin settings), so it can never contradict the booking page.
 */
const LINK = "font-bold text-fg underline decoration-accent decoration-2 underline-offset-4";

export function AboutTrack() {
  return (
    <section className="container-page py-24 md:py-32">
      <div className="grid gap-12 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <SectionHeading
            eyebrow={`کارتینگ ${site.city}`}
            title={
              <>
                پیست کارتینگ حرفه‌ای <span className="marker">داووس</span> در {site.city}
              </>
            }
          />
        </div>
        <div className="space-y-5 text-lg leading-9 text-fg-muted lg:col-span-7">
          <p>
            کارتینگ داووس یک پیست کارتینگ حرفه‌ای در {site.city}ه که با ماشین‌های <strong className="text-fg">تک‌نفره</strong> و{" "}
            <strong className="text-fg">دونفره</strong>، میزبان هیجان شماست. سانس‌های ما ۱۰ دقیقه‌ای هستن و دیوارهای لاستیکی دور مسیر،
            امنیت کامل رو برقرار می‌کنن. نقشه‌ی دقیق پیچ‌درپیچ پیست رو می‌تونید توی صفحهٔ{" "}
            <Link href="/track" className={LINK}>
              پیست کارتینگ {site.city}
            </Link>{" "}
            تماشا کنید.
          </p>
          <p>
            رزرو سانس‌ها کاملاً آنلاین انجام میشه؛ یعنی از روی جدول زمان‌بندی، روز و ساعت دلخواهتون رو انتخاب می‌کنید و بلیت می‌گیرید.
            رانندگی با کارتینگ تک‌نفره برای افراد بالای ۱۵ سال (بدون محدودیت قد) آزاد است. اگر دوست دارید از{" "}
            <Link href="/rules" className={LINK}>
              شرایط سنی و قد کارتینگ
            </Link>{" "}
            برای نوجوان‌ها و کودکان باخبر بشید یا جواب پرسش‌هاتون رو پیدا کنید، سری به بخش{" "}
            <Link href="/faq" className={LINK}>
              سوالات متداول
            </Link>{" "}
            بزنید.
          </p>
          <p>
            یادتون باشه که پیست ما روبازه و موقع بارندگی تعطیل میشه؛ پس حتماً قبل از رزرو، وضعیت آب‌وهوا رو چک کنید.{" "}
            <Link href="/contact" className={LINK}>
              آدرس و موقعیت دقیق روی نقشه
            </Link>{" "}
            رو هم می‌تونید توی صفحهٔ تماس ببینید.
          </p>
        </div>
      </div>
    </section>
  );
}
