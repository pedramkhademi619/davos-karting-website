import type { Metadata } from "next";
import { pageMetadata } from "@/lib/seo";
import { BookingWizard } from "@/components/booking/wizard/booking-wizard";
import { PageHero } from "@/components/page-hero";
import { BOOKING_HOME } from "@/lib/urls";

export const metadata: Metadata = pageMetadata({
  title: "رزرو آنلاین کارتینگ شیراز",
  description:
    "رزرو آنلاین کارتینگ شیراز: جای خالی سانس‌های پیست داووس را زنده ببینید، خودروی تک‌نفره یا دونفره را انتخاب کنید و بلیت را در یک دقیقه بگیرید.",
  path: BOOKING_HOME.startsWith("http") ? BOOKING_HOME : "/booking",
});

export default function BookingPage() {
  return (
    <>
      <PageHero
        eyebrow="رزرو آنلاین"
        title={
          <>
            رزرو <span className="glow-text">سانس</span>
          </>
        }
        lead="چهار قدم کوتاه: چند نفرید، کدوم روز، چه ساعتی، و ثبت. حدوداً یه دقیقه."
        compact
      />

      <section className="container-page py-8 md:py-14">
        <BookingWizard />
      </section>
    </>
  );
}
