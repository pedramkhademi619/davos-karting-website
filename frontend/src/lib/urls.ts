/**
 * Where each page lives. The main site (home, FAQ, contact), online booking (the booking page, sign-in, the
 * customer's tickets and the payment result) and the staff panel can run on three hosts: NEXT_PUBLIC_BOOKING_URL is
 * the booking subdomain (e.g. https://booking.davoskarting.ir) and NEXT_PUBLIC_ADMIN_URL the panel's
 * (e.g. https://admin.davoskarting.ir). Without them everything stays on one host: booking at /booking and the panel
 * at /admin (local development). The addresses are inlined at build time (frontend/Dockerfile, fed by compose from
 * .env); the main site's address is required.
 */

import { requiredEnv } from "@/lib/required-env";

const trim = (url: string | undefined) => (url ?? "").trim().replace(/\/+$/, "");

export const SITE_URL = trim(requiredEnv("PUBLIC_BASE_URL", process.env.NEXT_PUBLIC_SITE_URL));
export const BOOKING_URL = trim(process.env.NEXT_PUBLIC_BOOKING_URL);
export const ADMIN_URL = trim(process.env.NEXT_PUBLIC_ADMIN_URL);

function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname.toLowerCase();
  } catch {
    return "";
  }
}

export const SITE_HOSTNAME = hostnameOf(SITE_URL);
export const BOOKING_HOSTNAME = BOOKING_URL ? hostnameOf(BOOKING_URL) : "";
export const ADMIN_HOSTNAME = ADMIN_URL ? hostnameOf(ADMIN_URL) : "";

/** True when booking runs on its own subdomain. */
export const SPLIT_HOSTS = Boolean(BOOKING_HOSTNAME) && BOOKING_HOSTNAME !== SITE_HOSTNAME;

/** True when the staff panel runs on its own subdomain. */
export const ADMIN_SPLIT = Boolean(ADMIN_HOSTNAME) && ADMIN_HOSTNAME !== SITE_HOSTNAME;

/** Paths that belong to online booking. "/booking" is the booking page itself (the booking host's root). */
export function isBookingPath(path: string): boolean {
  return (
    path === "/booking" ||
    path.startsWith("/booking/") ||
    path === "/account" ||
    path.startsWith("/account/") ||
    path === "/login" ||
    path.startsWith("/payment/")
  );
}

/** "/booking" -> "/" on the booking host; other booking paths keep their path. */
export function bookingHostPath(path: string): string {
  return path === "/booking" ? "/" : path.replace(/^\/booking\//, "/");
}

/**
 * The href for an in-app path, as seen from the page being rendered: relative when the target is on the same host,
 * absolute when it lives on the other one.
 */
export function hrefFor(path: string, onBookingHost: boolean): string {
  if (!SPLIT_HOSTS) return path;
  const [pathname, query = ""] = path.split("?");
  const suffix = query ? `?${query}` : "";
  if (isBookingPath(pathname)) {
    const target = bookingHostPath(pathname) + suffix;
    return onBookingHost ? target : `${BOOKING_URL}${target}`;
  }
  return onBookingHost ? `${SITE_URL}${path}` : path;
}

/** The public address of the booking page (absolute when it is on the subdomain). */
export const BOOKING_HOME = SPLIT_HOSTS ? `${BOOKING_URL}/` : "/booking";

/** Is this request's Host (nginx forwards it without the port) the staff panel's subdomain? */
export function isAdminHostHeader(host: string | null): boolean {
  if (!ADMIN_SPLIT || !host) return false;
  return host.split(":")[0].toLowerCase() === ADMIN_HOSTNAME;
}

/** Where a link to the main site's own pages must point from the panel: absolute when the panel has its own host. */
export const SITE_HOME = ADMIN_SPLIT ? `${SITE_URL}/` : "/";

/** Is this request's Host (nginx forwards it without the port) the booking subdomain? */
export function isBookingHostHeader(host: string | null): boolean {
  if (!SPLIT_HOSTS || !host) return false;
  return host.split(":")[0].toLowerCase() === BOOKING_HOSTNAME;
}
