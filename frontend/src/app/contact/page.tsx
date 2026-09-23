import type { Metadata } from "next";
import { ButtonLink } from "@/components/button-link";
import { ClockIcon, PhoneIcon, PinIcon } from "@/components/icons";
import { InfoCard } from "@/components/info-card";
import { MapLink } from "@/components/map-link";
import { PageHero } from "@/components/page-hero";
import { PhoneLink } from "@/components/phone-link";
import { WorkingHours } from "@/components/working-hours";
import { site } from "@/content/site";

export const metadata: Metadata = {
  title: "تماس با ما",
  description: "راه‌های ارتباط با کارتینگ داوس: موقعیت پیست، ساعات کاری و تلفن رزرو.",
};

export default function ContactPage() {
  return (
    <>
      <PageHero eyebrow="ارتباط با ما" title="تماس با ما" lead="برای رزرو نوبت، پرسش یا هماهنگی با ما در ارتباط باشید." />

      <section className="container-page py-16 md:py-24">
        <div className="grid gap-5 sm:grid-cols-3">
          <InfoCard icon={PinIcon} label="موقعیت پیست">
            <MapLink />
          </InfoCard>
          <InfoCard icon={ClockIcon} label="ساعات کاری">
            <WorkingHours />
          </InfoCard>
          <InfoCard icon={PhoneIcon} label="تلفن رزرو">
            <PhoneLink />
          </InfoCard>
        </div>

        {/* No contact form on purpose: there is no ticket endpoint yet, and a form that silently does nothing is worse than none. */}
        <div className="mt-5 rounded-[2rem] border border-line bg-surface p-8 md:p-14">
          <h2 className="text-2xl font-black md:text-3xl">برای رزرو نوبت تماس بگیرید</h2>
          <p className="mt-4 max-w-xl text-fg-muted">{site.booking.rule}</p>
          <div className="mt-8 flex flex-wrap gap-4">
            <ButtonLink href={site.contact.phone.href}>{site.booking.callToAction}</ButtonLink>
            <ButtonLink href="/faq" variant="ghost" arrow={false}>
              سوالات متداول
            </ButtonLink>
          </div>
        </div>
      </section>
    </>
  );
}
