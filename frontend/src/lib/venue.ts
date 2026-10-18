/**
 * The venue's public facts that differ per deployment, from .env: CONTACT_PHONE, VENUE_LATITUDE and VENUE_LONGITUDE.
 * Compose passes them as NEXT_PUBLIC_* build arguments (frontend/Dockerfile), so they are inlined at build time; the
 * backend reads the same CONTACT_PHONE, so the site and the assistant always quote one number.
 *
 * A missing or malformed value stops the site with a clear message instead of publishing it without a phone number.
 */

import { requiredEnv } from "@/lib/required-env";

function coordinate(name: string, value: string | undefined, limit: number): number {
  const parsed = Number(requiredEnv(name, value));
  if (!Number.isFinite(parsed) || Math.abs(parsed) > limit) throw new Error(`${name} is not a valid coordinate.`);
  return parsed;
}

/** "09177334894", "+98 917 733 4894" or "989177334894" -> the local form "09177334894". */
function localPhone(raw: string): string {
  const digits = raw.replace(/\D/g, "");
  const local = digits.startsWith("98") ? `0${digits.slice(2)}` : digits;
  if (!/^0\d{10}$/.test(local)) throw new Error("CONTACT_PHONE must be an Iranian number such as 09177334894.");
  return local;
}

const local = localPhone(requiredEnv("CONTACT_PHONE", process.env.NEXT_PUBLIC_CONTACT_PHONE));
const latitude = coordinate("VENUE_LATITUDE", process.env.NEXT_PUBLIC_VENUE_LATITUDE, 90);
const longitude = coordinate("VENUE_LONGITUDE", process.env.NEXT_PUBLIC_VENUE_LONGITUDE, 180);

export const venue = {
  phone: {
    local, // 09177334894
    display: `${local.slice(0, 4)} ${local.slice(4, 7)} ${local.slice(7)}`, // 0917 733 4894
    href: `tel:${local}`,
    e164: `+98${local.slice(1)}`, // +989177334894, for search engines
  },
  geo: { latitude, longitude },
  mapHref: `https://www.google.com/maps?q=${latitude},${longitude}`,
} as const;
