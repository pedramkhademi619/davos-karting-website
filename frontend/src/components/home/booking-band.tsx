import { ButtonLink } from "@/components/button-link";
import { PhoneLink } from "@/components/phone-link";
import { site } from "@/content/site";

export function BookingBand() {
  return (
    <section className="container-page pb-24 md:pb-36">
      <div className="relative isolate overflow-hidden rounded-[2rem] bg-accent px-8 py-16 md:px-16 md:py-24">
        <div
          aria-hidden="true"
          className="checker-ink absolute inset-y-0 left-0 -z-10 w-1/2 opacity-[0.09] [mask-image:linear-gradient(to_right,black,transparent)]"
        />
        <div className="max-w-2xl">
          <p className="flex items-center gap-3 text-sm font-bold text-ink-soft">
            <span aria-hidden="true" className="h-[3px] w-8 rounded-full bg-ink" />
            رزرو تلفنی
          </p>
          <h2 className="mt-5 text-[clamp(2.25rem,6vw,4.5rem)] font-black leading-[1.15] text-ink">آماده یک دور تمام‌گاز هستید؟</h2>
          <p className="mt-6 max-w-lg text-lg text-ink-soft">{site.booking.rule}</p>
          <div className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-4">
            <ButtonLink href={site.contact.phone.href} variant="dark" size="lg">
              {site.booking.callToAction}
            </ButtonLink>
            <PhoneLink className="text-2xl font-black text-ink" />
          </div>
        </div>
      </div>
    </section>
  );
}
