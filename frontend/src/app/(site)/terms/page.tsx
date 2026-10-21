import type { Metadata } from "next";
import { ButtonLink } from "@/components/button-link";
import { PageHero } from "@/components/page-hero";
import { TermsSections } from "@/components/terms-sections";
import { site } from "@/content/site";

export const metadata: Metadata = {
  title: "قوانین و حریم خصوصی",
  description: "قوانین کارتینگ داووس: سن و قد، تعطیلی در بارندگی و بدی هوا، رزرو و پرداخت، ایمنی و حریم خصوصی.",
  alternates: { canonical: "/terms" },
};

export default function TermsPage() {
  return (
    <>
      <PageHero
        eyebrow="پیش از رزرو بخوانید"
        title="قوانین و حریم خصوصی"
        lead="با رزرو آنلاین، شما همین قوانین را می‌پذیرید. مهم‌ترین بخش‌ها سن و قد افراد و هوای بد است."
      />

      <section className="container-page py-16 md:py-24">
        <div className="mx-auto max-w-3xl">
          <TermsSections />
          <div className="mt-12 flex flex-wrap gap-4">
            <ButtonLink href={site.booking.href}>{site.booking.callToAction}</ButtonLink>
            <ButtonLink href="/rules" variant="ghost" arrow={false}>
              شرایط سوار شدن
            </ButtonLink>
          </div>
        </div>
      </section>
    </>
  );
}
