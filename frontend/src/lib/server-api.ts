import type { BookingInfo } from "@/lib/types";
import { requiredEnv } from "@/lib/required-env";
import { SITE_URL } from "@/lib/urls";

/**
 * Server-side reads from the API (inside compose the frontend reaches it at API_INTERNAL_URL, not through nginx).
 * Only public data is fetched here; anything tied to a customer is fetched by the browser with its own cookie.
 */

/** Set by docker-compose.yml (the API service on the private network). Read per request, at run time: it does not
 * exist while the site is being built. */
function internalApi(): string {
  return requiredEnv("API_INTERNAL_URL", process.env.API_INTERNAL_URL);
}

const INFO_TTL_MS = 5_000; // admin changes show up within seconds; a crowd does not turn every page view into an API call

let infoCache: { at: number; value: Promise<BookingInfo | null> } | null = null;

/** The public main-site address (sitemap, canonical URLs), from NEXT_PUBLIC_SITE_URL (see lib/urls.ts). */
export function siteUrl(): string {
  return SITE_URL;
}

async function fetchBookingInfo(): Promise<BookingInfo | null> {
  const url = `${internalApi()}/api/v1/reservations/info`; // a missing setting must fail loudly, not look like an outage
  try {
    const response = await fetch(url, {
      cache: "no-store",
      signal: AbortSignal.timeout(2500),
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return null;
    return (await response.json()) as BookingInfo;
  } catch {
    return null; // the page still renders; prices and counts are simply left out
  }
}

/**
 * Kart counts, prices and booking days from the admin panel; null when the API cannot answer quickly. Shared by all
 * requests in this process for a few seconds (concurrent renders wait for the same fetch); a failure is not kept.
 */
export async function getBookingInfo(): Promise<BookingInfo | null> {
  const now = Date.now();
  if (!infoCache || now - infoCache.at > INFO_TTL_MS) {
    const value = fetchBookingInfo();
    infoCache = { at: now, value };
    void value.then((result) => {
      if (result === null && infoCache?.value === value) infoCache = null;
    });
  }
  return infoCache.value;
}
