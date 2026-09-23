"use client";

import { usePathname } from "next/navigation";
import { useId, useState } from "react";
import { ButtonLink } from "@/components/button-link";
import { CloseIcon, MenuIcon } from "@/components/icons";
import { NavLinks } from "@/components/nav-links";
import { site } from "@/content/site";

export function MobileMenu() {
  const pathname = usePathname();
  // The menu is "open for" the page it was opened on, so navigating anywhere closes it without an effect.
  const [openFor, setOpenFor] = useState<string | null>(null);
  const open = openFor === pathname;
  const close = () => setOpenFor(null);
  const panelId = useId();

  return (
    <div className="md:hidden" onKeyDown={(event) => event.key === "Escape" && close()}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={open ? "بستن منو" : "باز کردن منو"}
        onClick={() => setOpenFor(open ? null : pathname)}
        className="grid h-11 w-11 place-items-center rounded-full border border-line-strong text-fg transition-colors hover:border-fg"
      >
        {open ? <CloseIcon className="h-5 w-5" /> : <MenuIcon className="h-5 w-5" />}
      </button>

      {/* Solid background on purpose: a blurred child inside the blurred header would not blur the page behind it. */}
      <div id={panelId} hidden={!open} className="absolute inset-x-0 top-full border-b border-line bg-canvas shadow-2xl">
        <nav aria-label="منوی موبایل" className="container-page pb-8 pt-2">
          <NavLinks
            onNavigate={close}
            className="flex flex-col"
            linkClassName="block border-b border-line py-5 text-xl font-bold text-fg transition-colors aria-[current=page]:underline aria-[current=page]:decoration-accent aria-[current=page]:decoration-4 aria-[current=page]:underline-offset-8"
          />
          <ButtonLink href={site.contact.phone.href} size="lg" className="mt-8 w-full">
            {site.booking.callToAction}
          </ButtonLink>
        </nav>
      </div>
    </div>
  );
}
