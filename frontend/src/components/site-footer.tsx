import Link from "next/link";
import { Logo } from "@/components/logo";
import { MapLink } from "@/components/map-link";
import { PhoneLink } from "@/components/phone-link";
import { WorkingHours } from "@/components/working-hours";
import { navigation, site } from "@/content/site";

export function SiteFooter() {
  // Jalali year in Persian digits.
  const year = new Intl.DateTimeFormat("fa-IR", { year: "numeric" }).format(new Date());

  return (
    <footer className="mt-auto border-t border-line bg-surface">
      <div className="container-page grid gap-12 py-16 md:grid-cols-12">
        <div className="md:col-span-5">
          <Logo />
          <p className="mt-6 max-w-sm text-fg-muted">تجربه‌ای مهیج و دقیق از رانندگی و رقابت روی پیست.</p>
        </div>

        <nav aria-label="پیوندهای پایین صفحه" className="md:col-span-3">
          <h2 className="text-base font-bold text-fg">صفحه‌ها</h2>
          <ul className="mt-5 space-y-3 text-fg-muted">
            {navigation.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="transition-colors hover:text-fg">
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <a href={site.contact.phone.href} className="transition-colors hover:text-fg">
                {site.booking.short}
              </a>
            </li>
          </ul>
        </nav>

        <div className="md:col-span-4">
          <h2 className="text-base font-bold text-fg">تماس</h2>
          <ul className="mt-5 space-y-3 text-fg-muted">
            <li>
              <MapLink className="transition-colors hover:text-fg" />
            </li>
            <li>
              <WorkingHours />
            </li>
            <li>
              <PhoneLink />
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-line">
        <p className="container-page py-6 text-sm text-fg-subtle">
          © {year} {site.name}. تمامی حقوق محفوظ است.
        </p>
      </div>
    </footer>
  );
}
