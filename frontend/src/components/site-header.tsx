import Link from "next/link";
import { ButtonLink } from "@/components/button-link";
import { UserIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { MobileMenu } from "@/components/mobile-menu";
import { NavLinks } from "@/components/nav-links";
import { navigation, site } from "@/content/site";
import { hrefFor } from "@/lib/urls";

const desktopLink =
  "relative block rounded-full px-4 py-2 text-[0.95rem] font-bold text-fg-muted transition-colors hover:text-fg " +
  "aria-[current=page]:bg-white/[0.08] aria-[current=page]:text-fg aria-[current=page]:shadow-[inset_0_1px_0_rgb(255_255_255/0.08)]";

/** `onBookingHost`: rendered on the booking subdomain, so main-site links become absolute (see lib/urls.ts). */
export function SiteHeader({ onBookingHost = false }: { onBookingHost?: boolean }) {
  const items = navigation.map((item) => ({ label: item.label, href: hrefFor(item.href, onBookingHost) }));
  const bookingHref = hrefFor("/booking", onBookingHost);
  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.07] bg-[#08090b]/75 backdrop-blur-xl backdrop-saturate-150">
      <div className="container-page flex h-16 items-center justify-between gap-3 md:h-[76px]">
        <Link href={hrefFor("/", onBookingHost)} aria-label={`${site.name}، صفحه اصلی`} className="rounded-xl">
          <Logo />
        </Link>

        <nav aria-label="منوی اصلی" className="hidden lg:block">
          <NavLinks items={items} className="flex items-center rounded-full border border-white/[0.08] bg-white/[0.03]" linkClassName={desktopLink} />
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href={hrefFor("/account", onBookingHost)}
            className="grid h-11 w-11 place-items-center rounded-full border border-white/15 bg-white/[0.04] text-fg transition-colors hover:border-accent hover:text-accent sm:flex sm:w-auto sm:gap-2 sm:px-4"
          >
            <UserIcon className="h-5 w-5" />
            <span className="sr-only sm:not-sr-only sm:text-sm sm:font-bold">حساب من</span>
          </Link>
          <ButtonLink href={bookingHref} size="sm" arrow={false} className="hidden sm:inline-flex">
            {site.booking.short}
          </ButtonLink>
          <MobileMenu items={items} bookingHref={bookingHref} />
        </div>
      </div>
    </header>
  );
}
