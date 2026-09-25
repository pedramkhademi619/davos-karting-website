import Link from "next/link";
import { ButtonLink } from "@/components/button-link";
import { Tacho } from "@/components/home/tacho";
import { CalendarIcon, KartIcon, ShieldIcon, TicketIcon } from "@/components/icons";
import { SpeedLines } from "@/components/speed-lines";
import { StartLights } from "@/components/start-lights";
import { site } from "@/content/site";
import { fa } from "@/lib/format";
import { stagger } from "@/lib/stagger";
import type { BookingInfo } from "@/lib/types";

const trust = [
  { icon: ShieldIcon, text: "درگاه رسمی بانک ملت" },
  { icon: TicketIcon, text: "بلیت و کد رزرو پیامکی" },
  { icon: CalendarIcon, text: "جای خالی زنده هر سانس" },
] as const;

/** Home hero: the headline on the paper canvas and a carbon "cockpit" with live readouts from the admin settings. */
export function Hero({ info }: { info: BookingInfo | null }) {
  return (
    <section className="relative isolate overflow-hidden">
      <div className="paper-glow" aria-hidden="true" />
      <div className="grain" aria-hidden="true" />

      <div className="container-page grid items-center gap-12 py-12 lg:min-h-[calc(100svh-90px)] lg:grid-cols-12 lg:gap-12 lg:py-16">
        <div className="min-w-0 lg:col-span-6">
          <p
            className="rise inline-flex items-center gap-3 rounded-full border border-line-strong bg-surface px-4 py-1.5 text-sm font-bold text-fg-muted shadow-sm"
            style={stagger(0)}
          >
            <span className="pulse-dot" aria-hidden="true" />
            {info?.online_booking_enabled === false ? "رزرو تلفنی نوبت" : "رزرو آنلاین سانس فعال است"}
          </p>

          <h1 className="rise mt-8 text-[clamp(3rem,7.4vw,6.2rem)] font-black leading-[1.08]" style={stagger(1)}>
            <span className="block">سرعت را</span>
            <span className="block">
              <span className="marker">جدی</span> بگیرید.
            </span>
          </h1>

          <p className="rise mt-8 max-w-lg text-lg text-fg-muted md:text-xl" style={stagger(2)}>
            پیست کارتینگ داوس؛ جایی برای رانندگی، رقابت و لذت سرعت. سانس دلخواه را مثل بلیت سینما انتخاب کنید، آنلاین بپردازید و
            پشت فرمان بنشینید.
          </p>

          <div className="rise mt-10 flex flex-wrap items-center gap-4" style={stagger(3)}>
            <ButtonLink href={site.booking.href} size="lg">
              {site.booking.callToAction}
            </ButtonLink>
            <ButtonLink href={site.contact.phone.href} variant="ghost" size="lg" arrow={false}>
              {site.booking.phoneCallToAction}
            </ButtonLink>
          </div>

          <ul className="rise mt-10 flex flex-wrap gap-x-6 gap-y-3 text-sm font-bold text-fg-muted" style={stagger(4)}>
            {trust.map(({ icon: IconComponent, text }) => (
              <li key={text} className="flex items-center gap-2">
                <IconComponent className="h-5 w-5 text-fg" />
                {text}
              </li>
            ))}
          </ul>
        </div>

        <div className="rise min-w-0 lg:col-span-6" style={stagger(2)}>
          <Cockpit info={info} />
        </div>
      </div>

      <div className="checker" aria-hidden="true" />
    </section>
  );
}

function Cockpit({ info }: { info: BookingInfo | null }) {
  const readouts = info
    ? [
        { label: "خودروی هر سانس", value: `${fa(info.single_capacity)} + ${fa(info.double_capacity)}`, note: "تک‌نفره + دونفره" },
        { label: "شروع سانس‌ها", value: fa(info.first_session), note: `هر ${fa(info.interval_minutes)} دقیقه` },
        {
          label: "رزرو",
          value: info.min_days_ahead === 0 ? "امروز" : "از روز قبل",
          note: info.closed_weekdays.length ? `جز ${info.closed_weekdays.join(" و ")}` : "همه روزها",
        },
      ]
    : [
        { label: "خودروها", value: "تک و دونفره", note: "برای همه سنین مجاز" },
        { label: "سانس‌ها", value: "هر روز", note: "جدول در صفحه رزرو" },
        { label: "رزرو", value: "آنلاین", note: "یا تلفنی" },
      ];

  return (
    <div className="carbon relative overflow-hidden rounded-[2.25rem] p-6 shadow-[0_50px_100px_-40px_rgb(12_13_16/0.8)] ring-1 ring-black/40 md:p-9">
      <SpeedLines />
      <div className="relative flex flex-wrap items-center justify-between gap-4">
        <StartLights />
        <span className="race-number rounded-full border border-white/15 px-3 py-1 text-[0.65rem] tracking-[0.3em] text-on-carbon-muted" dir="ltr">
          DAVOS · LIVE
        </span>
      </div>

      <div className="relative mt-8 grid items-center gap-8 sm:grid-cols-[1fr_auto]">
        <div>
          <p className="text-sm font-bold text-accent">پشت فرمان، چراغ‌ها که خاموش شد</p>
          <p className="mt-3 text-3xl font-black leading-snug md:text-4xl">
            سانس بعدی
            <br />
            مال شماست.
          </p>
        </div>
        <Tacho className="mx-auto h-40 w-40 md:h-48 md:w-48" />
      </div>

      <dl className="relative mt-8 grid grid-cols-3 gap-2 md:gap-3">
        {readouts.map((item) => (
          <div key={item.label} className="rounded-2xl bg-white/[0.06] p-3 ring-1 ring-white/10 md:p-4">
            <dt className="text-[0.7rem] font-bold text-on-carbon-muted md:text-xs">{item.label}</dt>
            <dd className="mt-2 text-lg font-black text-on-carbon md:text-2xl">{item.value}</dd>
            <dd className="mt-1 text-[0.7rem] text-on-carbon-muted md:text-xs">{item.note}</dd>
          </div>
        ))}
      </dl>

      <Link
        href={site.booking.href}
        className="group relative mt-6 flex items-center justify-between rounded-2xl bg-accent px-5 py-4 font-black text-ink transition-transform duration-300 hover:-translate-y-0.5"
      >
        <span className="flex items-center gap-3">
          <KartIcon className="h-6 w-6" />
          جدول سانس‌های خالی
        </span>
        <span aria-hidden="true" className="race-number text-sm transition-transform duration-300 group-hover:-translate-x-1">
          ←
        </span>
      </Link>
    </div>
  );
}
