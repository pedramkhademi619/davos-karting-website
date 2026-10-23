import Link from "next/link";
import { ButtonLink } from "@/components/button-link";
import { Logo } from "@/components/logo";
import { MapLink } from "@/components/map-link";
import { PhoneLink } from "@/components/phone-link";
import { WorkingHours } from "@/components/working-hours";
import type { BookingInfo } from "@/lib/types";
import { navigation, site } from "@/content/site";
import { hrefFor } from "@/lib/urls";

/** `onBookingHost`: rendered on the booking subdomain, so main-site links become absolute (see lib/urls.ts). */
export function SiteFooter({ onBookingHost = false, info = null }: { onBookingHost?: boolean; info?: BookingInfo | null }) {
  // Jalali year in Persian digits.
  const year = new Intl.DateTimeFormat("fa-IR", { year: "numeric" }).format(new Date());

  return (
    <footer className="carbon relative mt-auto overflow-hidden">
      <div className="checker opacity-90" aria-hidden="true" />
      <div className="container-page grid gap-12 py-16 md:grid-cols-12 md:py-20">
        <div className="md:col-span-5">
          <Logo tone="light" />
          <p className="mt-6 max-w-sm text-on-carbon-muted">
            پیست کارتینگ داووس، شیراز. سانس‌ها رو آنلاین رزرو کنید و بیاید پشت فرمون.
          </p>
          <ButtonLink href={hrefFor("/booking", onBookingHost)} className="mt-8">
            {site.booking.callToAction}
          </ButtonLink>
        </div>

        <nav aria-label="پیوندهای پایین صفحه" className="md:col-span-3">
          <h2 className="text-base font-bold text-on-carbon">صفحه‌ها</h2>
          <ul className="mt-5 space-y-3 text-on-carbon-muted">
            {navigation.map((item) => (
              <li key={item.href}>
                <Link href={hrefFor(item.href, onBookingHost)} className="transition-colors hover:text-accent">
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <Link href={hrefFor("/account", onBookingHost)} className="transition-colors hover:text-accent">
                حساب من و بلیت‌ها
              </Link>
            </li>
            <li>
              <Link href={hrefFor("/terms", onBookingHost)} className="transition-colors hover:text-accent">
                قوانین و حریم خصوصی
              </Link>
            </li>
          </ul>
        </nav>

        <div className="md:col-span-4">
          <h2 className="text-base font-bold text-on-carbon">تماس</h2>
          <ul className="mt-5 space-y-3 text-on-carbon-muted">
            <li>
              <MapLink className="transition-colors hover:text-accent" />
            </li>
            <li>
              <WorkingHours info={info} />
            </li>
            {site.contact.phone && (
              <li>
                <PhoneLink className="font-bold text-on-carbon" />
              </li>
            )}
          </ul>
        </div>
      </div>

      <div className="border-t border-carbon-line">
        <div className="container-page flex flex-col gap-2 py-6 text-sm text-on-carbon-muted sm:flex-row sm:items-center sm:justify-between">
          <p>
            © {year} {site.name}. تمامی حقوق محفوظ است.
          </p>
          <p className="flex items-center gap-2">
            <span aria-hidden="true" className="h-2 w-2 rounded-full bg-go" />
            {site.city}، بلوار مهرگان، شهرک بهاران
          </p>
        </div>
      </div>
    </footer>
  );
}
