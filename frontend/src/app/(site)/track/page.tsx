import type { Metadata } from "next";
import { breadcrumbs, pageMetadata } from "@/lib/seo";
import { JsonLd } from "@/components/json-ld";
import { ButtonLink } from "@/components/button-link";
import { FlagIcon, PinIcon, ShieldIcon } from "@/components/icons";
import { TrackMapLazy } from "@/components/home/track-map-lazy";
import { MapLink } from "@/components/map-link";
import { PageHero } from "@/components/page-hero";
import { site } from "@/content/site";

export const metadata: Metadata = pageMetadata({
  title: "پیست کارتینگ شیراز؛ نقشه و مسیر",
  description:
    "نقشه‌ی پیست کارتینگ داووس در شیراز از نمای بالا: پیچ به پیچ مسیر، خط شروع و پایان، دیواره لاستیکی دور تا دور و مسیریابی روی نقشه تا پیست.",
  path: "/track",
});

const features = [
  { icon: FlagIcon, title: "خط شروع و پایان", text: "کنار سکوی تماشاچی‌هاست؛ هر دور از همین‌جا شمرده میشه." },
  { icon: ShieldIcon, title: "دیواره لاستیکی", text: "دور تا دور مسیر لاستیک‌های زرد و قرمز چیدیم." },
  { icon: PinIcon, title: "مسیریابی", text: "موقعیت پیست رو روی نقشه ببینید:" },
] as const;

export default function TrackPage() {
  return (
    <>
      <JsonLd data={breadcrumbs("پیست", "/track")} />
      <PageHero eyebrow="پیست" title="پیچ به پیچ، از بالا" />

      <section className="container-page py-16 md:py-24">
        <div className="grid items-start gap-12 lg:grid-cols-12">
          <ul className="space-y-6 lg:col-span-4">
            {features.map(({ icon: IconComponent, title, text }) => (
              <li key={title} className="flex gap-4">
                <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-accent text-ink">
                  <IconComponent className="h-6 w-6" />
                </span>
                <div>
                  <h2 className="text-lg font-black">{title}</h2>
                  <p className="text-fg-muted">
                    {text} {title === "مسیریابی" && <MapLink className="font-bold text-fg" />}
                  </p>
                </div>
              </li>
            ))}
            <li>
              <ButtonLink href={site.booking.href}>{site.booking.callToAction}</ButtonLink>
            </li>
          </ul>
          <div className="lg:col-span-8">
            <TrackMapLazy />
          </div>
        </div>
      </section>
    </>
  );
}
