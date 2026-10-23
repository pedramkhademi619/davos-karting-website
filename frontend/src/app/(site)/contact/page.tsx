import type { Metadata } from "next";
import { breadcrumbs, pageMetadata } from "@/lib/seo";
import { JsonLd } from "@/components/json-ld";
import { ButtonLink } from "@/components/button-link";
import { ClockIcon, PhoneIcon, PinIcon } from "@/components/icons";
import { InfoCard } from "@/components/info-card";
import { MapLink } from "@/components/map-link";
import { PageHero } from "@/components/page-hero";
import { PhoneLink } from "@/components/phone-link";
import { WorkingHours } from "@/components/working-hours";
import { site } from "@/content/site";
import { getBookingInfo } from "@/lib/server-api";

export const metadata: Metadata = pageMetadata({
  title: "آدرس و تماس با کارتینگ داووس شیراز",
  description:
    "آدرس و موقعیت پیست کارتینگ داووس در شیراز روی نقشه، ساعات کاری شیفت صبح و عصر و شماره تماس برای رزرو تلفنی و هماهنگی گروه‌ها.",
  path: "/contact",
});

export default async function ContactPage() {
  const info = await getBookingInfo();
  return (
    <>
      <JsonLd data={breadcrumbs("تماس با ما", "/contact")} />
      <PageHero eyebrow="ارتباط با ما" title="تماس با ما" lead="برای رزرو، سوال یا هماهنگی گروهی با ما در تماس باشید." />

      <section className="container-page py-16 md:py-24">
        <div className={`grid gap-5 ${site.contact.phone ? "sm:grid-cols-3" : "sm:grid-cols-2"}`}>
          <InfoCard headingLevel={2} icon={PinIcon} label="موقعیت پیست">
            <MapLink />
          </InfoCard>
          <InfoCard headingLevel={2} icon={ClockIcon} label="ساعات کاری">
            <WorkingHours info={info} />
          </InfoCard>
          {site.contact.phone && (
            <InfoCard headingLevel={2} icon={PhoneIcon} label="تلفن رزرو">
              <PhoneLink />
            </InfoCard>
          )}
        </div>

        {/* No contact form on purpose: there is no ticket endpoint yet, and a form that silently does nothing is worse than none. */}
        <div className="carbon mt-5 overflow-hidden rounded-[2rem] p-8 md:p-14">
          <h2 className="text-2xl font-black md:text-3xl">سریع‌ترین راه: رزرو آنلاین</h2>
          <p className="mt-4 max-w-xl text-on-carbon-muted">
            ببینید کدوم سانس‌ها جا دارن و همون‌جا رزرو کنید. برای گروه‌های بزرگ یا هماهنگی خاص، زنگ بزنید.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <ButtonLink href={site.booking.href}>{site.booking.callToAction}</ButtonLink>
            {site.contact.phone && (
              <ButtonLink href={site.contact.phone.href} variant="ghost-light" arrow={false}>
                {site.booking.phoneCallToAction}
              </ButtonLink>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
