import { BookingBand } from "@/components/home/booking-band";
import { Club } from "@/components/home/club";
import { ContactPreview } from "@/components/home/contact-preview";
import { Experience } from "@/components/home/experience";
import { FaqPreview } from "@/components/home/faq-preview";
import { Hero } from "@/components/home/hero";
import { Marquee } from "@/components/marquee";
import { marqueeWords } from "@/content/site";

export default function HomePage() {
  return (
    <>
      <Hero />
      <Marquee words={marqueeWords} />
      <Experience />
      <BookingBand />
      <Club />
      <FaqPreview />
      <ContactPreview />
    </>
  );
}
