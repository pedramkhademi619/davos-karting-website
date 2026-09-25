import { ButtonLink } from "@/components/button-link";
import { SectionHeading } from "@/components/section-heading";
import { ridingRules } from "@/content/site";

/** The owner's riding rules at a glance (the assistant checks the details for each family). */
export function RidingRules() {
  return (
    <section className="relative isolate overflow-hidden border-y border-line bg-surface py-24 md:py-32">
      <div className="container-page">
        <div className="flex flex-col justify-between gap-8 lg:flex-row lg:items-end">
          <SectionHeading
            eyebrow="چه کسی پشت فرمان؟"
            title="شرایط سوار شدن، خیلی ساده"
            lead="ایمنی اول است. اگر مطمئن نیستید، از دستیار هوشمند پایین صفحه بپرسید؛ سن، قد، روز و ساعت را برایتان دقیق چک می‌کند."
          />
          <ButtonLink href="/faq" variant="ghost">
            جزئیات کامل
          </ButtonLink>
        </div>

        <ul className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {ridingRules.map((rule) => (
            <li key={rule.title} className="reveal group rounded-[1.75rem] border border-line bg-canvas p-7 transition-colors duration-300 hover:border-fg">
              <span dir="ltr" className="race-number inline-block rounded-xl bg-ink px-3 py-1.5 text-lg font-black text-accent">
                {rule.badge}
              </span>
              <h3 className="mt-6 text-xl font-black">{rule.title}</h3>
              <p className="mt-3 text-fg-muted">{rule.text}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
