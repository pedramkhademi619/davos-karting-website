import type { Metadata } from "next";
import { breadcrumbs, pageMetadata } from "@/lib/seo";
import { JsonLd } from "@/components/json-ld";
import { ButtonLink } from "@/components/button-link";
import { PageHero } from "@/components/page-hero";
import { site } from "@/content/site";
import { ridingRulesFor } from "@/lib/hours";
import { getBookingInfo } from "@/lib/server-api";

export const metadata: Metadata = pageMetadata({
  title: "شرایط سنی و قد کارتینگ شیراز",
  description:
    "شرایط سنی و قد کارتینگ داووس شیراز: رانندگی تک‌نفره از ۱۵ سال، شرایط نوجوان‌های ۱۱ تا ۱۴ سال، خودروی دونفره با راننده‌ی گواهینامه‌دار و کودکان ۴ تا ۱۴ سال.",
  path: "/rules",
});

export default async function RulesPage() {
  const rules = ridingRulesFor(await getBookingInfo());
  return (
    <>
      <JsonLd data={breadcrumbs("شرایط سوار شدن", "/rules")} />
      <PageHero
        eyebrow="کی می‌تونه پشت فرمون بشینه؟"
        title="شرایط سوار شدن"
      />

      <section className="container-page py-16 md:py-24">
        <ul className="grid gap-5 sm:grid-cols-2">
          {rules.map((rule) => (
            <li key={rule.title} className="panel p-8">
              <span dir="ltr" className="race-number inline-block rounded-xl bg-ink px-3 py-1.5 text-lg font-black text-accent">
                {rule.badge}
              </span>
              <h2 className="mt-6 text-xl font-black">{rule.title}</h2>
              <p className="mt-3 leading-8 text-fg-muted">{rule.text}</p>
            </li>
          ))}
        </ul>

        <div className="carbon mt-5 overflow-hidden rounded-[2rem] p-8 md:p-12">
          <h2 className="text-2xl font-black md:text-3xl">اگه هوا بد بشه چی؟</h2>
          <p className="mt-4 max-w-2xl leading-8 text-on-carbon-muted">
            پیست روبازه و با بارون یا هوای بد تعطیل میشه. اون موقع پول برنمی‌گرده و رزروتون به یه روز دیگه منتقل میشه؛ پس قبل از
            رزرو حتماً هوا رو چک کنید.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <ButtonLink href="/terms">متن کامل قوانین و حریم خصوصی</ButtonLink>
            <ButtonLink href={site.booking.href} variant="ghost-light" arrow={false}>
              {site.booking.callToAction}
            </ButtonLink>
          </div>
        </div>
      </section>
    </>
  );
}
