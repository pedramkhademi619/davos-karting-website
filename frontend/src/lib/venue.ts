/**
 * The venue's public facts that differ per deployment, from .env: CONTACT_PHONE, VENUE_LATITUDE and VENUE_LONGITUDE.
 * Compose passes them as NEXT_PUBLIC_* build arguments (frontend/Dockerfile), so they are inlined at build time; the
 * backend reads the same CONTACT_PHONE, so the site and the assistant always quote one number.
 *
 * CONTACT_PHONE may be left empty (a test copy of the site shows no number at all, so nobody calls the real venue about
 * it); a malformed number or a missing coordinate still stops the site with a clear message.
 */

import { requiredEnv } from "@/lib/required-env";

function coordinate(name: string, value: string | undefined, limit: number): number {
  const parsed = Number(requiredEnv(name, value));
  if (!Number.isFinite(parsed) || Math.abs(parsed) > limit) throw new Error(`${name} is not a valid coordinate.`);
  return parsed;
}

/** "09179190993", "+98 917 919 0993" or "989179190993" -> the local form "09179190993". */
function localPhone(raw: string): string {
  const digits = raw.replace(/\D/g, "");
  const local = digits.startsWith("98") ? `0${digits.slice(2)}` : digits;
  if (!/^0\d{10}$/.test(local)) throw new Error("CONTACT_PHONE must be an Iranian number such as 09179190993.");
  return local;
}

const rawPhone = (process.env.NEXT_PUBLIC_CONTACT_PHONE ?? "").trim();
const local = rawPhone ? localPhone(rawPhone) : null;
const latitude = coordinate("VENUE_LATITUDE", process.env.NEXT_PUBLIC_VENUE_LATITUDE, 90);
const longitude = coordinate("VENUE_LONGITUDE", process.env.NEXT_PUBLIC_VENUE_LONGITUDE, 180);

export const venue = {
  /** null when no number is published. */
  phone: local
    ? {
        local, // 09179190993
        display: `${local.slice(0, 4)} ${local.slice(4, 7)} ${local.slice(7)}`, // 0917 919 0993
        href: `tel:${local}`,
        e164: `+98${local.slice(1)}`, // +989179190993, for search engines
      }
    : null,
  geo: { latitude, longitude },
  mapHref: `https://www.google.com/maps?q=${latitude},${longitude}`,
};
