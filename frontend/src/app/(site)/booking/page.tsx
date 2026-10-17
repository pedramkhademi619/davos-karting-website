import type { Metadata } from "next";
import { BookingWizard } from "@/components/booking/wizard/booking-wizard";
import { PageHero } from "@/components/page-hero";
import { BOOKING_HOME } from "@/lib/urls";

export const metadata: Metadata = {
  title: "رزرو آنلاین سانس",
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
            یک دور تا <span className="glow-text">پشت فرمان</span>
          </>
        }
        lead="بگویید چه کسانی می‌آیند؛ خودروها، روز و سانس مناسب را با هم پیدا می‌کنیم. هر مرحله یک سکتور است."
        compact
      />

      <section className="container-page py-8 md:py-14">
        <BookingWizard />
      </section>
    </>
  );
}
