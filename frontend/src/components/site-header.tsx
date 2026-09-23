import Link from "next/link";
import { ButtonLink } from "@/components/button-link";
import { Logo } from "@/components/logo";
import { MobileMenu } from "@/components/mobile-menu";
import { NavLinks } from "@/components/nav-links";
import { site } from "@/content/site";

const desktopLink =
  "relative py-2 text-[0.95rem] font-medium text-fg-muted transition-colors hover:text-fg aria-[current=page]:text-fg " +
  "after:absolute after:inset-x-0 after:-bottom-1 after:h-[3px] after:origin-right after:rounded-full after:scale-x-0 after:bg-accent " +
  "after:transition-transform after:duration-300 hover:after:scale-x-100 aria-[current=page]:after:scale-x-100";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-canvas/85 backdrop-blur-md">
      <div className="container-page flex h-[72px] items-center justify-between gap-4">
        <Link href="/" aria-label={`${site.name}، صفحه اصلی`} className="rounded-xl">
          <Logo />
        </Link>

        <nav aria-label="منوی اصلی" className="hidden md:block">
          <NavLinks className="flex items-center gap-9" linkClassName={desktopLink} />
        </nav>

        <div className="flex items-center gap-3">
          <ButtonLink href={site.contact.phone.href} size="sm" arrow={false}>
            {site.booking.short}
          </ButtonLink>
          <MobileMenu />
        </div>
      </div>
    </header>
  );
}
