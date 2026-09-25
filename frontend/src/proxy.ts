import { NextResponse, type NextRequest } from "next/server";
import { BOOKING_URL, SITE_URL, bookingHostPath, isBookingHostHeader, isBookingPath, SPLIT_HOSTS } from "@/lib/urls";

/**
 * Two jobs, before any page renders:
 *
 * 1. Hosts. With a booking subdomain (NEXT_PUBLIC_BOOKING_URL), booking pages live only there and the main site's pages
 *    only on the main host; a request on the wrong host is redirected. On the booking host "/" shows the booking page.
 *
 * 2. Content-Security-Policy with a fresh nonce per request (the pattern from Next.js' CSP guide). The admin panel and
 *    the payment flow live on these origins, so only scripts carrying this request's nonce (and what they load, via
 *    'strict-dynamic') may run. form-action allows the bank's payment page: Bank Mellat (Behpardakht) is reached by
 *    POSTing a form to bpm.shaparak.ir. Styles keep 'unsafe-inline' because React renders style attributes.
 */
const BANK_FORM_TARGETS = "https://bpm.shaparak.ir";

function policy(nonce: string): string {
  const isDev = process.env.NODE_ENV === "development";
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' blob: data:",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    `form-action 'self' ${BANK_FORM_TARGETS}`,
    "frame-ancestors 'none'",
  ].join("; ");
}

/** Where a request that is on the wrong host should go, or null when it is on the right one. */
function hostRedirect(request: NextRequest, onBookingHost: boolean): string | null {
  if (!SPLIT_HOSTS) return null;
  const { pathname, search } = request.nextUrl;
  if (pathname.startsWith("/_next")) return null;
  if (onBookingHost) {
    if (pathname === "/booking") return `${BOOKING_URL}/${search}`;
    if (pathname === "/" || isBookingPath(pathname)) return null;
    return `${SITE_URL}${pathname}${search}`; // FAQ, contact, admin... belong to the main site
  }
  if (isBookingPath(pathname)) return `${BOOKING_URL}${bookingHostPath(pathname)}${search}`;
  return null;
}

export function proxy(request: NextRequest) {
  const onBookingHost = isBookingHostHeader(request.headers.get("host"));
  const redirect = hostRedirect(request, onBookingHost);
  if (redirect) {
    const permanent = request.nextUrl.pathname === "/booking";
    return NextResponse.redirect(redirect, permanent ? 308 : 307);
  }

  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const csp = policy(nonce);
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);
  requestHeaders.set("x-davos-host", onBookingHost ? "booking" : "site");

  const response =
    onBookingHost && request.nextUrl.pathname === "/"
      ? NextResponse.rewrite(new URL("/booking", request.url), { request: { headers: requestHeaders } })
      : NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  response.headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()");
  response.headers.set("Cross-Origin-Opener-Policy", "same-origin");
  return response;
}

export const config = {
  // Pages only: the API is proxied by nginx before it ever reaches Next.js, and static files need no policy.
  // Prefetches are NOT skipped: on the booking host "/" must be rewritten for them too, or a prefetched "/" would be the
  // main site's home page.
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|icon.svg|robots.txt|sitemap.xml).*)"],
};
