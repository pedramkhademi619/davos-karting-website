import { ButtonLink } from "@/components/button-link";
import { PhoneLink } from "@/components/phone-link";
import { SpeedLines } from "@/components/speed-lines";
import { StartLights } from "@/components/start-lights";
import { site } from "@/content/site";

export function BookingBand() {
  return (
    <section className="container-page pb-24 md:pb-32">
      <div className="carbon relative isolate overflow-hidden rounded-[2.5rem] px-8 py-16 md:px-16 md:py-24">
        <SpeedLines />
        <div aria-hidden="true" className="checker-bw flag-wave absolute inset-y-0 left-0 -z-10 w-1/3 opacity-[0.08] [mask-image:linear-gradient(to_right,black,transparent)]" />
        <div className="relative max-w-2xl">
          <StartLights />
          <h2 className="mt-8 text-[clamp(2.4rem,6vw,4.6rem)] font-black leading-[1.1]">آماده یک دور تمام‌گاز هستید؟</h2>
          <p className="mt-6 max-w-lg text-lg text-on-carbon-muted">
            جای خالی سانس‌ها را زنده ببینید، خودروی دلخواه را انتخاب کنید و در کمتر از یک دقیقه بلیتتان را بگیرید.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-4">
            <ButtonLink href={site.booking.href} size="lg">
              {site.booking.callToAction}
            </ButtonLink>
            <span className="text-on-carbon-muted">
              یا تماس: <PhoneLink className="text-xl font-black text-on-carbon" />
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
