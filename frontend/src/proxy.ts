import { NextResponse, type NextRequest } from "next/server";
import {
  ADMIN_SPLIT,
  ADMIN_URL,
  BOOKING_URL,
  SITE_URL,
  SPLIT_HOSTS,
  bookingHostPath,
  isAdminHostHeader,
  isBookingHostHeader,
  isBookingPath,
} from "@/lib/urls";

/**
 * Two jobs, before any page renders:
 *
 * 1. Hosts. With a booking subdomain (NEXT_PUBLIC_BOOKING_URL), booking pages live only there and the main site's pages
 *    only on the main host; a request on the wrong host is redirected. On the booking host "/" shows the booking page.
 *    With a staff panel subdomain (NEXT_PUBLIC_ADMIN_URL) the panel lives only there, at "/", and nothing else does.
 *
 * 2. Content-Security-Policy with a fresh nonce per request (the pattern from Next.js' CSP guide). The admin panel and
 *    the payment flow live on these origins, so only scripts carrying this request's nonce (and what they load, via
 *    'strict-dynamic') may run. form-action allows the bank's payment page: Bank Mellat (Behpardakht) is reached by
 *    POSTing a form to it. Its address is the backend's MELLAT_START_PAY_URL from .env, handed to this container as
 *    BANK_PAYMENT_URL (read at run time, not inlined). Styles keep 'unsafe-inline' because React renders style attributes.
 */
function originOf(url: string | undefined): string {
  try {
    return url ? new URL(url).origin : "";
  } catch {
    return "";
  }
}

const BANK_FORM_TARGET = originOf(process.env.BANK_PAYMENT_URL);

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
    `form-action 'self'${BANK_FORM_TARGET ? ` ${BANK_FORM_TARGET}` : ""}`,
    "frame-ancestors 'none'",
  ].join("; ");
}

/** Where a request that is on the wrong host should go, or null when it is on the right one. */
function hostRedirect(request: NextRequest, onBookingHost: boolean, onAdminHost: boolean): string | null {
  const { pathname, search } = request.nextUrl;
  if (pathname.startsWith("/_next")) return null;
  const isPanelPath = pathname === "/admin" || pathname.startsWith("/admin/");
  if (onAdminHost) {
    if (pathname === "/") return null; // the panel itself (rewritten to /admin below)
    if (isPanelPath) return `${ADMIN_URL}/`; // the panel has no path of its own on its host
    return `${SITE_URL}${pathname}${search}`; // everything else belongs to the main site
  }
  if (ADMIN_SPLIT && isPanelPath) return `${ADMIN_URL}/`;
  if (!SPLIT_HOSTS) return null;
  if (onBookingHost) {
    if (pathname === "/booking") return `${BOOKING_URL}/${search}`;
    if (pathname === "/" || isBookingPath(pathname)) return null;
    return `${SITE_URL}${pathname}${search}`; // FAQ, contact, admin... belong to the main site
  }
  if (isBookingPath(pathname)) return `${BOOKING_URL}${bookingHostPath(pathname)}${search}`;
  return null;
}

export function proxy(request: NextRequest) {
  const host = request.headers.get("host");
  const onBookingHost = isBookingHostHeader(host);
  const onAdminHost = isAdminHostHeader(host);
  const redirect = hostRedirect(request, onBookingHost, onAdminHost);
  if (redirect) {
    const permanent = request.nextUrl.pathname === "/booking";
    return NextResponse.redirect(redirect, permanent ? 308 : 307);
  }

  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const csp = policy(nonce);
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);
  requestHeaders.set("x-davos-host", onAdminHost ? "admin" : onBookingHost ? "booking" : "site");

  const rewriteTarget = request.nextUrl.pathname === "/" ? (onBookingHost ? "/booking" : onAdminHost ? "/admin" : null) : null;
  const response = rewriteTarget
    ? NextResponse.rewrite(new URL(rewriteTarget, request.url), { request: { headers: requestHeaders } })
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
