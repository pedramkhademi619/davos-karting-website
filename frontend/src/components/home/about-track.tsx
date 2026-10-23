import Link from "next/link";
import { SectionHeading } from "@/components/section-heading";
import { site } from "@/content/site";

/**
 * A short, plain description of the business for people (and search engines) who arrive by searching "کارتینگ شیراز":
 * what it is, where, what to expect and where to read more. Only facts that are true for every deployment (nothing
 * from the admin settings), so it can never contradict the booking page.
 */
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
            کارتینگ داووس یک پیست کارتینگ حرفه‌ای در {site.city} است؛ با خودروهای <strong className="text-fg">تک‌نفره</strong> و{" "}
            <strong className="text-fg">دونفره</strong>، سانس‌های ۱۰ دقیقه‌ای و دیواره‌ی لاستیکی دور تا دور مسیر. نقشه‌ی پیست را پیچ به پیچ
            در صفحه‌ی <Link href="/track" className="font-bold text-fg underline decoration-accent decoration-2 underline-offset-4">پیست کارتینگ {site.city}</Link> ببینید.
          </p>
          <p>
            سانس را آنلاین رزرو می‌کنید: می‌گویید چه کسانی می‌آیند، روز و ساعت را از روی جدول انتخاب می‌کنید و بلیت را می‌گیرید. رانندگی
            تک‌نفره از ۱۵ سال به بالا بدون شرط قد و ساعت آزاد است؛ شرایط نوجوان‌ها و کودکان را در{" "}
            <Link href="/rules" className="font-bold text-fg underline decoration-accent decoration-2 underline-offset-4">شرایط سنی و قد کارتینگ</Link> و پاسخ
            پرسش‌های رایج را در <Link href="/faq" className="font-bold text-fg underline decoration-accent decoration-2 underline-offset-4">سوالات متداول</Link> بخوانید.
          </p>
          <p>
            پیست روباز است و با بارندگی تعطیل می‌شود؛ پیش از رزرو آب‌وهوا را بررسی کنید.{" "}
            <Link href="/contact" className="font-bold text-fg underline decoration-accent decoration-2 underline-offset-4">آدرس و موقعیت پیست روی نقشه</Link> در
            صفحه‌ی تماس است.
          </p>
        </div>
      </div>
    </section>
  );
}
