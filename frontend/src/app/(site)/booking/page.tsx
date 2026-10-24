import type { Metadata } from "next";
import { pageMetadata } from "@/lib/seo";
import { BookingWizard } from "@/components/booking/wizard/booking-wizard";
import { PageHero } from "@/components/page-hero";
import { BOOKING_HOME } from "@/lib/urls";

export const metadata: Metadata = pageMetadata({
  title: "رزرو آنلاین کارتینگ شیراز",
  description:
    "رزرو آنلاین کارتینگ شیراز: ببینید کدام سانس‌های پیست داووس جای خالی دارند، خودروی تک‌نفره یا دونفره را انتخاب کنید و در یک دقیقه بلیت بگیرید.",
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
        compact
      />

      <section className="container-page py-8 md:py-14">
        <BookingWizard />
      </section>
    </>
  );
}
