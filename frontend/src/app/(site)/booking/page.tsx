import type { Metadata } from "next";
import { BookingWizard } from "@/components/booking/wizard/booking-wizard";
import { PageHero } from "@/components/page-hero";
import { BOOKING_HOME } from "@/lib/urls";

export const metadata: Metadata = {
  title: "رزرو آنلاین کارتینگ شیراز",
  description: "جای خالی سانس‌های کارتینگ داووس را زنده ببینید، خودروی تک‌نفره یا دونفره انتخاب کنید و از درگاه بانک ملت بپردازید.",
  alternates: { canonical: BOOKING_HOME },
};

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
        lead="چهار قدم کوتاه: چند نفرید، کدام روز، چه ساعتی، و پرداخت. حدود یک دقیقه."
        compact
      />

      <section className="container-page py-8 md:py-14">
        <BookingWizard />
      </section>
    </>
  );
}
