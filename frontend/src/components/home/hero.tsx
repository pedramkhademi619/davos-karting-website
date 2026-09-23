import { ButtonLink } from "@/components/button-link";
import { TrackMap } from "@/components/track-map";
import { site } from "@/content/site";
import { stagger } from "@/lib/stagger";

export function Hero() {
  return (
    <section className="relative isolate overflow-hidden">
      <div className="hero-bg" aria-hidden="true" />
      <div className="grain" aria-hidden="true" />

      <div className="container-page grid items-center gap-12 py-14 lg:min-h-[calc(100svh-86px)] lg:grid-cols-12 lg:gap-10 lg:py-16">
        <div className="lg:col-span-5">
          <p
            className="rise inline-flex items-center gap-3 rounded-full border border-line-strong bg-surface px-4 py-1.5 text-sm text-fg-muted shadow-sm"
            style={stagger(0)}
          >
            <span className="pulse-dot" aria-hidden="true" />
            رزرو تلفنی نوبت
          </p>

          <h1 className="rise mt-8 text-[clamp(2.75rem,6vw,5.25rem)] font-black leading-[1.2]" style={stagger(1)}>
            <span className="block">سرعت را</span>
            <span className="block">
              <span className="marker">جدی</span> بگیرید
            </span>
          </h1>

          <p className="rise mt-8 max-w-md text-lg text-fg-muted md:text-xl" style={stagger(2)}>
            کارتینگ داوس؛ جایی برای رانندگی، رقابت و لذت سرعت. برای رزرو نوبت تماس بگیرید و پشت فرمان بنشینید.
          </p>

          <div className="rise mt-10 flex flex-wrap items-center gap-4" style={stagger(3)}>
            <ButtonLink href={site.contact.phone.href} size="lg">
              {site.booking.callToAction}
            </ButtonLink>
            <ButtonLink href="/faq" variant="ghost" size="lg" arrow={false}>
              سوالات متداول
            </ButtonLink>
          </div>
        </div>

        <div className="rise lg:col-span-7" style={stagger(2)}>
          <TrackMap />
        </div>
      </div>

      <div className="checker" aria-hidden="true" />
    </section>
  );
}
