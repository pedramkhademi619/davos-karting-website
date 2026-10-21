import type { Metadata } from "next";
import { ButtonLink } from "@/components/button-link";
import { PageHero } from "@/components/page-hero";
import { site } from "@/content/site";
import { ridingRulesFor } from "@/lib/hours";
import { getBookingInfo } from "@/lib/server-api";

export const metadata: Metadata = {
  title: "شرایط سوار شدن",
  description: "چه کسی پشت فرمان می‌نشیند؟ شرایط سن و قد برای خودروهای تک‌نفره و دونفره کارتینگ داووس.",
  alternates: { canonical: "/rules" },
};

export default async function RulesPage() {
  const rules = ridingRulesFor(await getBookingInfo());
  return (
    <>
      <PageHero
        eyebrow="چه کسی پشت فرمان؟"
        title="شرایط سوار شدن"
        lead="سن و قد را همین‌جا چک کنید؛ در رزرو هم از شما تأیید می‌گیریم که سن‌ها درست وارد شده است."
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
          <h2 className="text-2xl font-black md:text-3xl">هوا بد شد چه می‌شود؟</h2>
          <p className="mt-4 max-w-2xl leading-8 text-on-carbon-muted">
            پیست روباز است و با بارندگی یا بدی هوا تعطیل می‌شود. در این حالت پولی برگردانده نمی‌شود و رزرو شما به روز دیگری منتقل می‌شود؛ پس پیش از
            رزرو آب‌وهوا را بررسی کنید.
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
