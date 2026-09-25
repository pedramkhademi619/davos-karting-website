import type { Metadata } from "next";
import { BookingApp } from "@/components/booking/booking-app";
import { ShieldIcon, SmsIcon, TicketIcon } from "@/components/icons";
import { PageHero } from "@/components/page-hero";
import { BOOKING_HOME } from "@/lib/urls";

export const metadata: Metadata = {
  title: "رزرو آنلاین سانس",
  description: "جای خالی سانس‌های کارتینگ داوس را زنده ببینید، خودروی تک‌نفره یا دونفره انتخاب کنید و از درگاه بانک ملت بپردازید.",
  alternates: { canonical: BOOKING_HOME },
};

const promises = [
  { icon: TicketIcon, text: "انتخاب سانس مثل بلیت سینما" },
  { icon: ShieldIcon, text: "پرداخت امن در درگاه بانک ملت" },
  { icon: SmsIcon, text: "کد رزرو پیامکی" },
] as const;

export default function BookingPage() {
  return (
    <>
      <PageHero eyebrow="رزرو آنلاین" title="سانس خودت را انتخاب کن" lead="روز، ساعت و تعداد خودرو را انتخاب کنید؛ بقیه‌اش با ما.">
        <ul className="flex flex-wrap gap-x-6 gap-y-3 text-sm font-bold text-on-carbon-muted">
          {promises.map(({ icon: IconComponent, text }) => (
            <li key={text} className="flex items-center gap-2">
              <IconComponent className="h-5 w-5 text-accent" />
              {text}
            </li>
          ))}
        </ul>
      </PageHero>

      <section className="container-page py-12 md:py-16">
        <BookingApp />
      </section>
    </>
  );
}
