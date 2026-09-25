import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/server-api";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/", disallow: ["/admin", "/account", "/login", "/payment/", "/api/"] },
    sitemap: `${siteUrl()}/sitemap.xml`,
  };
}
