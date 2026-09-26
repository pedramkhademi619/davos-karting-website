import type { Metadata } from "next";
import { BookingApp } from "@/components/booking/booking-app";
import { PageHero } from "@/components/page-hero";
import { BOOKING_HOME } from "@/lib/urls";

export const metadata: Metadata = {
  title: "رزرو آنلاین سانس",
  description: "جای خالی سانس‌های کارتینگ داوس را زنده ببینید، خودروی تک‌نفره یا دونفره انتخاب کنید و از درگاه بانک ملت بپردازید.",
  alternates: { canonical: BOOKING_HOME },
};

export default function BookingPage() {
  return (
    <>
      <PageHero eyebrow="رزرو آنلاین" title="سانس خودت را انتخاب کن" lead="روز، ساعت و تعداد خودرو را انتخاب کنید؛ بقیه‌اش با ما." />

      <section className="container-page py-12 md:py-16">
        <BookingApp />
      </section>
    </>
  );
}
