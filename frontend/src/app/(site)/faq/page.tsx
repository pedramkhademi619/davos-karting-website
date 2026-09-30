import type { Metadata } from "next";
import { ButtonLink } from "@/components/button-link";
import { FaqList } from "@/components/faq-list";
import { JsonLd } from "@/components/json-ld";
import { PageHero } from "@/components/page-hero";
import { buildFaq } from "@/content/faq";
import { site } from "@/content/site";
import { getBookingInfo } from "@/lib/server-api";

export const metadata: Metadata = {
  title: "سوالات متداول",
  description: "رزرو آنلاین، قیمت‌ها، ظرفیت سانس‌ها و شرایط سنی و قد برای خودروهای تک‌نفره و دونفره کارتینگ داوس.",
  alternates: { canonical: "/faq" },
};

export default async function FaqPage() {
  const items = buildFaq(await getBookingInfo());

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "FAQPage",
          mainEntity: items.map((item) => ({
            "@type": "Question",
            name: item.question,
            acceptedAnswer: { "@type": "Answer", text: item.answer },
          })),
        }}
      />
      <PageHero eyebrow="پشتیبانی" title="سوالات متداول" lead="پاسخ رایج‌ترین پرسش‌ها پیش از رزرو سانس." />

      <section className="container-page py-16 md:py-24">
        <div className="mx-auto max-w-3xl">
          <FaqList items={items} />

          <div className="carbon mt-16 rounded-[2rem] p-8 text-center md:p-14">
            <h2 className="text-2xl font-black md:text-3xl">پاسخ خود را پیدا نکردید؟</h2>
            <p className="mx-auto mt-4 max-w-md text-on-carbon-muted">
              از دستیار هوشمند پایین صفحه بپرسید؛ شرایط خانواده یا گروهتان را دقیق حساب می‌کند. یا با ما تماس بگیرید.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-4">
              <ButtonLink href={site.booking.href}>{site.booking.callToAction}</ButtonLink>
              <ButtonLink href="/contact" variant="ghost-light" arrow={false}>
                تماس با ما
              </ButtonLink>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
