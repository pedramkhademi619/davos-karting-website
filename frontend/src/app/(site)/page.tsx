import { BookingBand } from "@/components/home/booking-band";
import { ContactPreview } from "@/components/home/contact-preview";
import { AboutTrack } from "@/components/home/about-track";
import { Experience } from "@/components/home/experience";
import { FaqPreview } from "@/components/home/faq-preview";
import { Hero } from "@/components/home/hero";
import { HowItWorks } from "@/components/home/how-it-works";
import { RidingRules } from "@/components/home/riding-rules";
import { JsonLd } from "@/components/json-ld";
import { Marquee } from "@/components/marquee";
import { buildFaq } from "@/content/faq";
import { number } from "@/lib/format";
import { marqueeWords, site } from "@/content/site";
import { getBookingInfo, siteUrl } from "@/lib/server-api";
import { BOOKING_HOME, SITE_URL } from "@/lib/urls";
import type { Metadata } from "next";
import { SHARE_IMAGE } from "@/lib/seo";

const homeTitle = `کارتینگ ${site.city} | پیست کارتینگ حرفه‌ای داووس`;

export const metadata: Metadata = {
  title: { absolute: homeTitle },
  description: site.description,
  alternates: { canonical: SITE_URL },
  openGraph: {
    type: "website",
    locale: "fa_IR",
    siteName: site.name,
    title: homeTitle,
    description: site.description,
    url: SITE_URL,
    images: [SHARE_IMAGE],
  },
  twitter: { card: "summary_large_image", title: homeTitle, description: site.description, images: [SHARE_IMAGE.url] },
};

export default async function HomePage() {
  const info = await getBookingInfo();
  const url = siteUrl();

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "SportsActivityLocation",
          "@id": `${url}/#venue`,
          name: site.name,
          image: `${url}/opengraph-image.png`,
          parentOrganization: { "@id": `${url}/#organization` },
          alternateName: site.nameLatin,
          description: site.description,
          address: {
            "@type": "PostalAddress",
            streetAddress: site.streetAddress,
            addressLocality: site.city,
            addressRegion: site.region,
            addressCountry: "IR",
          },
          ...(site.sameAs.length ? { sameAs: site.sameAs } : {}),
          areaServed: site.city,
          sport: "Karting",
          url,
          ...(site.contact.phone ? { telephone: site.contact.phone.e164 } : {}),
          geo: { "@type": "GeoCoordinates", latitude: site.contact.geo.latitude, longitude: site.contact.geo.longitude },
          hasMap: [site.contact.map.href, site.contact.neshan.href],
          // The price of one kart for one session, cheapest to dearest, from the admin panel's prices.
          ...(info
            ? {
                priceRange: `${number(Math.min(info.normal_single_toman, info.holiday_single_toman))} تا ${number(
                  Math.max(info.normal_double_toman, info.holiday_double_toman),
                )} تومان`,
                currenciesAccepted: "IRR",
              }
            : {}),
          openingHoursSpecification: [
            ...(info?.morning_shift_enabled
              ? [
                  {
                    "@type": "OpeningHoursSpecification",
                    dayOfWeek: ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    opens: info.morning_first_session,
                    closes: info.morning_last_session_before,
                  },
                ]
              : []),
            ...site.contact.openingHours.map(({ schemaDays, opens, closes }) => ({
              "@type": "OpeningHoursSpecification",
              dayOfWeek: schemaDays,
              opens,
              closes,
            })),
          ],
          potentialAction: { "@type": "ReserveAction", target: BOOKING_HOME.startsWith("http") ? BOOKING_HOME : `${url}${BOOKING_HOME}` },
        }}
      />
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "Organization",
              "@id": `${url}/#organization`,
              name: site.name,
              alternateName: site.nameLatin,
              url,
              logo: `${url}/logo.png`,
              ...(site.sameAs.length ? { sameAs: site.sameAs } : {}),
              ...(site.contact.phone
                ? {
                    contactPoint: {
                      "@type": "ContactPoint",
                      telephone: site.contact.phone.e164,
                      contactType: "customer service",
                      areaServed: "IR",
                      availableLanguage: "fa",
                    },
                  }
                : {}),
            },
            {
              "@type": "WebSite",
              "@id": `${url}/#website`,
              url,
              name: site.name,
              alternateName: [site.nameLatin, `کارتینگ ${site.city}`],
              inLanguage: "fa-IR",
              publisher: { "@id": `${url}/#organization` },
            },
          ],
        }}
      />
      <Hero info={info} />
      <Marquee words={marqueeWords} />
      <AboutTrack />
      <Experience />
      <HowItWorks />
      <RidingRules info={info} />
      <FaqPreview items={buildFaq(info)} />
      <ContactPreview info={info} />
      <BookingBand />
    </>
  );
}
