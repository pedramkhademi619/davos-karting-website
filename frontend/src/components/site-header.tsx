import Link from "next/link";
import { ButtonLink } from "@/components/button-link";
import { UserIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { MobileMenu } from "@/components/mobile-menu";
import { NavLinks } from "@/components/nav-links";
import { navigation, site } from "@/content/site";
import { hrefFor } from "@/lib/urls";

const desktopLink =
  "relative py-2 text-[0.95rem] font-bold text-fg-muted transition-colors hover:text-fg aria-[current=page]:text-fg " +
  "after:absolute after:inset-x-0 after:-bottom-1 after:h-[3px] after:origin-right after:rounded-full after:scale-x-0 after:bg-accent " +
  "after:transition-transform after:duration-300 hover:after:scale-x-100 aria-[current=page]:after:scale-x-100";

/** `onBookingHost`: rendered on the booking subdomain, so main-site links become absolute (see lib/urls.ts). */
export function SiteHeader({ onBookingHost = false }: { onBookingHost?: boolean }) {
  const items = navigation.map((item) => ({ label: item.label, href: hrefFor(item.href, onBookingHost) }));
  const bookingHref = hrefFor("/booking", onBookingHost);
  return (
    <header className="sticky top-0 z-50 border-b border-line/80 bg-canvas/80 backdrop-blur-xl backdrop-saturate-150">
      <div className="container-page flex h-[76px] items-center justify-between gap-4">
        <Link href={hrefFor("/", onBookingHost)} aria-label={`${site.name}، صفحه اصلی`} className="rounded-xl">
          <Logo />
        </Link>

        <nav aria-label="منوی اصلی" className="hidden lg:block">
          <NavLinks items={items} className="flex items-center gap-9" linkClassName={desktopLink} />
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href={hrefFor("/account", onBookingHost)}
            className="grid h-11 w-11 place-items-center rounded-full border border-line-strong text-fg transition-colors hover:border-fg sm:flex sm:w-auto sm:gap-2 sm:px-4"
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
