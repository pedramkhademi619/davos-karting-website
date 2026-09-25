import { BookingBand } from "@/components/home/booking-band";
import { ContactPreview } from "@/components/home/contact-preview";
import { Experience } from "@/components/home/experience";
import { FaqPreview } from "@/components/home/faq-preview";
import { Hero } from "@/components/home/hero";
import { HowItWorks } from "@/components/home/how-it-works";
import { RidingRules } from "@/components/home/riding-rules";
import { TrackSection } from "@/components/home/track-section";
import { JsonLd } from "@/components/json-ld";
import { Marquee } from "@/components/marquee";
import { buildFaq } from "@/content/faq";
import { marqueeWords, site } from "@/content/site";
import { getBookingInfo, siteUrl } from "@/lib/server-api";
import { BOOKING_HOME } from "@/lib/urls";

export default async function HomePage() {
  const info = await getBookingInfo();
  const url = siteUrl();

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "SportsActivityLocation",
          name: site.name,
          alternateName: site.nameLatin,
          description: site.description,
          url,
          telephone: site.contact.phone.e164,
          geo: { "@type": "GeoCoordinates", latitude: site.contact.geo.latitude, longitude: site.contact.geo.longitude },
          hasMap: site.contact.map.href,
          openingHoursSpecification: [
            {
              "@type": "OpeningHoursSpecification",
              dayOfWeek: ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday"],
              opens: "15:00",
              closes: "24:00",
            },
            { "@type": "OpeningHoursSpecification", dayOfWeek: ["Thursday", "Friday"], opens: "15:00", closes: "01:00" },
          ],
          potentialAction: { "@type": "ReserveAction", target: BOOKING_HOME.startsWith("http") ? BOOKING_HOME : `${url}${BOOKING_HOME}` },
        }}
      />
      <Hero info={info} />
      <Marquee words={marqueeWords} />
      <Experience />
      <HowItWorks />
      <TrackSection />
      <RidingRules />
      <FaqPreview items={buildFaq(info)} />
      <ContactPreview />
      <BookingBand />
    </>
  );
}
