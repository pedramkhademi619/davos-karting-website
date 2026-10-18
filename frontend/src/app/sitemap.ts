import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/server-api";
import { BOOKING_HOME } from "@/lib/urls";

/** Public pages only; the account, payment and admin screens are not for search engines. */
export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteUrl();
  const now = new Date();
  return [
    { url: `${base}/`, lastModified: now, changeFrequency: "weekly", priority: 1 },
    { url: BOOKING_HOME.startsWith("http") ? BOOKING_HOME : `${base}${BOOKING_HOME}`, lastModified: now, changeFrequency: "daily", priority: 0.9 },
    { url: `${base}/faq`, lastModified: now, changeFrequency: "monthly", priority: 0.7 },
    { url: `${base}/contact`, lastModified: now, changeFrequency: "yearly", priority: 0.5 },
  ];
}
