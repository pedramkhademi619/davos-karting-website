import { SectionHeading } from "@/components/section-heading";
import { club } from "@/content/site";

/** Marketing teaser only: sign-up and points are not built yet, so the section says so instead of linking nowhere. */
export function Club() {
  return (
    <section className="container-page pb-24 md:pb-36">
      <div className="club-card relative overflow-hidden rounded-[2rem] border border-gold/25 p-8 md:p-16">
        <span className="absolute end-6 top-6 rounded-full border border-gold/40 bg-white/70 px-4 py-1 text-sm font-bold text-gold md:end-10 md:top-10">
          به‌زودی
        </span>
        <div className="max-w-2xl">
          <SectionHeading eyebrow="باشگاه مشتریان" title={club.title} lead={club.text} tone="gold" />
        </div>
        <ul className="mt-10 flex flex-wrap gap-3">
          {club.benefits.map((benefit) => (
            <li key={benefit} className="rounded-full border border-gold/30 bg-white/70 px-5 py-2 font-medium text-gold">
              {benefit}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
