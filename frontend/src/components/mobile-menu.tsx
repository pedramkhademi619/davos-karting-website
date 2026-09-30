"use client";

import { usePathname } from "next/navigation";
import { useId, useState } from "react";
import { ButtonLink } from "@/components/button-link";
import { CloseIcon, MenuIcon } from "@/components/icons";
import { NavLinks, type NavItem } from "@/components/nav-links";
import { PhoneLink } from "@/components/phone-link";
import { site } from "@/content/site";

export function MobileMenu({ items, bookingHref }: { items: readonly NavItem[]; bookingHref: string }) {
  const pathname = usePathname();
  // The menu is "open for" the page it was opened on, so navigating anywhere closes it without an effect.
  const [openFor, setOpenFor] = useState<string | null>(null);
  const open = openFor === pathname;
  const close = () => setOpenFor(null);
  const panelId = useId();

  return (
    <div className="lg:hidden" onKeyDown={(event) => event.key === "Escape" && close()}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={open ? "بستن منو" : "باز کردن منو"}
        onClick={() => setOpenFor(open ? null : pathname)}
        className="grid h-11 w-11 place-items-center rounded-full bg-ink text-white transition-transform active:scale-95"
      >
        {open ? <CloseIcon className="h-5 w-5" /> : <MenuIcon className="h-5 w-5" />}
      </button>

      {/* Solid background on purpose: a blurred child inside the blurred header would not blur the page behind it. */}
      <div id={panelId} hidden={!open} className="carbon absolute inset-x-0 top-full border-b border-carbon-line shadow-2xl">
        <nav aria-label="منوی موبایل" className="container-page pb-10 pt-4">
          <NavLinks
            items={items}
            onNavigate={close}
            className="flex flex-col"
            linkClassName="flex items-center justify-between border-b border-carbon-line py-5 text-2xl font-black text-on-carbon transition-colors aria-[current=page]:text-accent"
          />
          <ButtonLink href={bookingHref} size="lg" className="mt-8 w-full">
            {site.booking.callToAction}
          </ButtonLink>
          <p className="mt-6 text-center text-on-carbon-muted">
            یا تماس: <PhoneLink className="font-bold text-on-carbon" />
          </p>
        </nav>
      </div>
    </div>
  );
}
