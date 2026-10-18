"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { KartIcon, PhoneIcon } from "@/components/icons";
import { site } from "@/content/site";

/** Pages with their own bottom bar (or where booking is the page itself) do not get this one. */
const HIDDEN_ON = ["/booking", "/login", "/account"];

/**
 * Phone-only bar fixed to the bottom of the screen: book a session, or call. Not on the booking subdomain, which is the
 * booking page itself (served at "/" there).
 */
export function MobileCta({ bookingHref, onBookingHost }: { bookingHref: string; onBookingHost: boolean }) {
  const pathname = usePathname();
  if (onBookingHost || HIDDEN_ON.some((path) => pathname.startsWith(path))) return null;
  return (
    <>
      <div className="h-24 lg:hidden" aria-hidden="true" />
      <nav aria-label="رزرو سریع" className="mobile-cta flex items-center gap-2 p-2 lg:hidden">
        <Link
          href={bookingHref}
          className="shine flex h-13 flex-1 items-center justify-center gap-2 rounded-2xl bg-accent px-4 text-base font-black text-ink shadow-[0_10px_30px_-10px_rgb(255_196_0/0.8)] active:scale-[0.98]"
        >
          <KartIcon className="h-5 w-5" />
          {site.booking.callToAction}
        </Link>
        <a
          href={site.contact.phone.href}
          aria-label={`تماس: ${site.contact.phone.display}`}
          className="grid h-13 w-13 place-items-center rounded-2xl border border-white/15 text-on-carbon active:scale-95"
        >
          <PhoneIcon className="h-5 w-5" />
        </a>
      </nav>
    </>
  );
}
