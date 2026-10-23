import { ButtonLink } from "@/components/button-link";
import { ClockIcon, PhoneIcon, PinIcon } from "@/components/icons";
import { InfoCard } from "@/components/info-card";
import { MapLink } from "@/components/map-link";
import { PhoneLink } from "@/components/phone-link";
import { site } from "@/content/site";
import { SectionHeading } from "@/components/section-heading";
import { WorkingHours } from "@/components/working-hours";
import type { BookingInfo } from "@/lib/types";

export function ContactPreview({ info }: { info: BookingInfo | null }) {
  return (
    <section className="container-page pb-24 md:pb-32">
      <div className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
        <SectionHeading eyebrow="تماس با ما" title="آدرس و ساعت کاری" />
        <ButtonLink href="/contact" variant="ghost">
          راه‌های تماس
        </ButtonLink>
      </div>
      <div className="mt-12 grid gap-5 md:grid-cols-3">
        <InfoCard icon={PinIcon} label="موقعیت پیست">
          <MapLink />
        </InfoCard>
        <InfoCard icon={ClockIcon} label="ساعات کاری">
          <WorkingHours info={info} />
        </InfoCard>
        {site.contact.phone && (
          <InfoCard icon={PhoneIcon} label="تلفن رزرو">
            <PhoneLink />
          </InfoCard>
        )}
      </div>
    </section>
  );
}
