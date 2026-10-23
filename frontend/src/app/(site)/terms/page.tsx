import type { Metadata } from "next";
import { breadcrumbs, pageMetadata } from "@/lib/seo";
import { JsonLd } from "@/components/json-ld";
import { ButtonLink } from "@/components/button-link";
import { PageHero } from "@/components/page-hero";
import { TermsSections } from "@/components/terms-sections";
import { site } from "@/content/site";

export const metadata: Metadata = pageMetadata({
  title: "قوانین و حریم خصوصی",
  description:
    "قوانین کارتینگ داووس شیراز پیش از رزرو: سن و قد سواران، تعطیلی در بارندگی و انتقال رزرو، رزرو و پرداخت، ایمنی در پیست و حریم خصوصی اطلاعات شما.",
  path: "/terms",
});

export default function TermsPage() {
  return (
    <>
      <JsonLd data={breadcrumbs("قوانین و حریم خصوصی", "/terms")} />
      <PageHero
        eyebrow="قبل از رزرو بخونید"
        title="قوانین و حریم خصوصی"
        lead="هر کی آنلاین رزرو می‌کنه، همین قوانین رو قبول کرده. مهم‌ترین‌هاش سن و قد آدم‌ها و هوای بده."
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
