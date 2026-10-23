import { ButtonLink } from "@/components/button-link";
import { TrackMapLazy } from "@/components/home/track-map-lazy";
import { CalendarIcon, ShieldIcon, TicketIcon } from "@/components/icons";
import { StartLights } from "@/components/start-lights";
import { site } from "@/content/site";
import { fa } from "@/lib/format";
import { stagger } from "@/lib/stagger";
import type { BookingInfo } from "@/lib/types";

const trust = [
  { icon: ShieldIcon, text: "درگاه رسمی بانک ملت" },
  { icon: TicketIcon, text: "بلیت و کد پیامکی" },
  { icon: CalendarIcon, text: "جای خالی زنده" },
] as const;

/**
 * Home hero on full-strength carbon fibre with a light sweeping over it: the headline in polished metal, and the real
 * Davos circuit seen from above (the aerial-photo map, two karts lapping), under smoked-glass live readouts from the
 * admin settings.
 */
export function Hero({ info }: { info: BookingInfo | null }) {
  const readouts = info
    ? [
        { label: "خودرو در هر سانس", value: fa(info.single_capacity + info.double_capacity), unit: "دستگاه" },
        { label: "شروع سانس‌ها", value: fa(info.morning_shift_enabled ? info.morning_first_session : info.first_session), unit: `هر ${fa(info.interval_minutes)} دقیقه` },
        { label: "از قیمت", value: fa(Math.round(info.normal_single_toman / 1000)), unit: "هزار تومان" },
      ]
    : [
        { label: "خودروها", value: "۲", unit: "نوع" },
        { label: "سانس‌ها", value: "هر روز", unit: "از عصر" },
        { label: "رزرو", value: "آنلاین", unit: "یا تلفنی" },
      ];

  return (
    <section className="carbon-weave relative isolate overflow-hidden">
      <div className="sheen" aria-hidden="true" />
      <div className="vignette" aria-hidden="true" />

      <div className="container-page grid items-center gap-10 pb-12 pt-8 md:pt-12 lg:min-h-[calc(100svh-91px)] lg:grid-cols-12 lg:gap-8 lg:py-10">
        <div className="relative z-10 min-w-0 lg:col-span-6">
          <p className="rise glass inline-flex items-center gap-3 rounded-full px-4 py-1.5 text-sm font-bold text-on-carbon-muted" style={stagger(0)}>
            <span className="pulse-dot" aria-hidden="true" />
            {info?.online_booking_enabled === false ? "رزرو تلفنی نوبت" : "رزرو آنلاین سانس فعال است"}
          </p>

          <h1 className="rise mt-7 text-[clamp(3.1rem,min(13vw,11.5svh),6.6rem)] font-black leading-[1.02] md:mt-9" style={stagger(1)}>
            <span className="chrome-text block">سرعت را</span>
            <span className="block">
              <span className="glow-text">جدی</span> <span className="chrome-text">بگیرید.</span>
            </span>
          </h1>

          <p className="rise mt-6 max-w-lg text-[1.05rem] leading-8 text-on-carbon-muted md:mt-8 md:text-xl md:leading-9" style={stagger(2)}>
            کارتینگ داووس، پیست کارتینگ حرفه‌ای شیراز؛ جایی برای رانندگی، رقابت و لذت سرعت. بگویید چه کسانی می‌آیند، سانس را از روی جدول استارت بردارید و پشت
            فرمان بنشینید.
          </p>

          <div className="rise mt-8 flex flex-col gap-3 sm:flex-row sm:items-center md:mt-10" style={stagger(3)}>
            <ButtonLink href={site.booking.href} size="lg" className="w-full sm:w-auto">
              {site.booking.callToAction}
            </ButtonLink>
            {site.contact.phone && (
              <ButtonLink href={site.contact.phone.href} variant="ghost-light" size="lg" arrow={false} className="w-full sm:w-auto">
                {site.booking.phoneCallToAction}
              </ButtonLink>
            )}
          </div>

          <ul className="rise mt-8 flex flex-wrap gap-x-5 gap-y-2.5 text-sm font-bold text-on-carbon-muted" style={stagger(4)}>
            {trust.map(({ icon: IconComponent, text }) => (
              <li key={text} className="flex items-center gap-2">
                <IconComponent className="h-[1.1rem] w-[1.1rem] text-accent" />
                {text}
              </li>
            ))}
          </ul>
        </div>

        {/* On a computer the hero is exactly one screen: 91px is the header (77) and the chequered strip (14), so the
            strip sits on the screen's bottom edge. The map is sized by the screen's height as well as the column's width
            (430px is the header, the padding, the start lights, the caption and the readouts; 1.32 is the map's
            width/height, content/track.ts), and the headline by the height too, so short laptop screens fit. */}
        <div className="rise relative min-w-0 lg:col-span-6 lg:mx-auto lg:w-[min(100%,max(360px,calc((100svh-430px)*1.32)))]" style={stagger(2)}>
          <div className="relative">
            {/* Floodlight glow under the track. */}
            <div aria-hidden="true" className="absolute inset-[8%] -z-10 rounded-full bg-accent/15 blur-3xl" />
            <div className="glass float-y mb-3 w-fit rounded-2xl px-3 py-2 sm:px-4 sm:py-3">
              <StartLights />
            </div>
            <TrackMapLazy />
          </div>

          <dl className="mt-4 grid grid-cols-3 gap-2 sm:gap-3">
            {readouts.map((item) => (
              <div key={item.label} className="glass rounded-2xl p-3 sm:p-4">
                <dt className="text-[0.68rem] font-bold text-on-carbon-muted sm:text-xs">{item.label}</dt>
                <dd className="mt-1.5 text-xl font-black leading-none text-on-carbon sm:text-3xl">{item.value}</dd>
                <dd className="mt-1.5 text-[0.66rem] text-on-carbon-muted sm:text-xs">{item.unit}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      <div className="checker" aria-hidden="true" />
    </section>
  );
}
