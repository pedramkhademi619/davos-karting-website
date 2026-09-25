import { ButtonLink } from "@/components/button-link";
import { SectionHeading } from "@/components/section-heading";
import { SpeedLines } from "@/components/speed-lines";
import { bookingSteps, site } from "@/content/site";
import { fa } from "@/lib/format";

/** Four steps of online booking on a carbon band, joined by a dashed racing line. */
export function HowItWorks() {
  return (
    <section className="carbon relative isolate overflow-hidden py-24 md:py-32">
      <SpeedLines />
      <div className="container-page relative">
        <div className="flex flex-col justify-between gap-8 lg:flex-row lg:items-end">
          <SectionHeading
            eyebrow="رزرو آنلاین"
            title="مثل خرید بلیت سینما، فقط سریع‌تر"
            lead="چهار قدم تا پشت فرمان؛ بدون تماس، بدون انتظار."
            onCarbon
          />
          <ButtonLink href={site.booking.href} size="lg">
            شروع رزرو
          </ButtonLink>
        </div>

        <ol className="relative mt-16 grid gap-10 md:grid-cols-4 md:gap-6">
          <span
            aria-hidden="true"
            className="absolute inset-x-8 top-8 hidden border-t-2 border-dashed border-white/20 md:block"
          />
          {bookingSteps.map((step, index) => (
            <li key={step.title} className="reveal relative">
              <span className="relative grid h-16 w-16 place-items-center rounded-full bg-carbon ring-[6px] ring-white/10">
                <span className="grid h-12 w-12 place-items-center rounded-full bg-accent text-xl font-black text-ink">{fa(index + 1)}</span>
              </span>
              <h3 className="mt-6 text-2xl font-black">{step.title}</h3>
              <p className="mt-3 max-w-xs text-on-carbon-muted">{step.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
