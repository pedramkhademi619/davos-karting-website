import type { Metadata } from "next";
import { site } from "@/content/site";
import { SITE_URL } from "@/lib/urls";

/** The brand as it closes every page title ("… | داووس کارتینگ"), from the root layout's title template. */
export const BRAND = site.name;

/**
 * The share picture (app/opengraph-image.png, 1200x630). Named explicitly: Next.js drops the file-based image from a
 * page that sets its own openGraph/twitter fields, and every public page does.
 */
export const SHARE_IMAGE = { url: "/opengraph-image.png", width: 1200, height: 630, alt: "کارتینگ شیراز؛ پیست کارتینگ حرفه‌ای داووس" };

type PageSeo = {
  /** The page's own title (the layout adds " | داووس کارتینگ"). */
  title: string;
  /** 120–160 characters: what the page offers, in the words people search with. */
  description: string;
  /** The page's address: a path on the main site ("/faq") or a full address on another host (the booking page). */
  path: string;
};

/**
 * Title, description, canonical address and the social-sharing tags of one public page, all from one place so they
 * never disagree.
 */
export function pageMetadata({ title, description, path }: PageSeo): Metadata {
  const url = path.startsWith("http") ? path : `${SITE_URL}${path === "/" ? "" : path}`;
  const fullTitle = `${title} | ${BRAND}`;
  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: { type: "website", locale: "fa_IR", siteName: BRAND, title: fullTitle, description, url, images: [SHARE_IMAGE] },
    twitter: { card: "summary_large_image", title: fullTitle, description, images: [SHARE_IMAGE.url] },
  };
}

/** A private page (account, sign-in, payment result): no canonical address and kept out of search results. */
export function privateMetadata(title: string): Metadata {
  return { title, robots: { index: false, follow: false } };
}

/** schema.org BreadcrumbList for an inner page: Home › this page. */
export function breadcrumbs(name: string, path: string) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "خانه", item: `${SITE_URL}/` },
      { "@type": "ListItem", position: 2, name, item: `${SITE_URL}${path}` },
    ],
  };
}
