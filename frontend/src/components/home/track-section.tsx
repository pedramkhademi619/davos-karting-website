import { FlagIcon, PinIcon, ShieldIcon } from "@/components/icons";
import { MapLink } from "@/components/map-link";
import { SectionHeading } from "@/components/section-heading";
import { TrackMapLazy } from "@/components/home/track-map-lazy";

const features = [
  { icon: FlagIcon, title: "خط شروع و پایان", text: "کنار سکوی تماشاگران؛ هر دور از همان‌جا شمرده می‌شود." },
  { icon: ShieldIcon, title: "دیواره لاستیکی", text: "دور تا دور مسیر با لاستیک‌های زرد و قرمز محافظت شده است." },
  { icon: PinIcon, title: "مسیریابی", text: "موقعیت دقیق پیست را روی نقشه ببینید." },
] as const;

export function TrackSection() {
  return (
    <section className="container-page py-24 md:py-32">
      <div className="grid items-center gap-14 lg:grid-cols-12">
        <div className="lg:col-span-4">
          <SectionHeading
            eyebrow="پیست"
            title="پیچ به پیچ، از نمای بالا"
            lead="نقشه پیست داوس از روی تصویر هوایی؛ دو کارت کوچک روی نقشه مسیر را دور می‌زنند."
          />
          <ul className="mt-10 space-y-6">
            {features.map(({ icon: IconComponent, title, text }) => (
              <li key={title} className="flex gap-4">
                <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-accent text-ink">
                  <IconComponent className="h-6 w-6" />
                </span>
                <div>
                  <h3 className="text-lg font-black">{title}</h3>
                  <p className="text-fg-muted">
                    {text} {title === "مسیریابی" && <MapLink className="font-bold text-fg" />}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <div className="reveal lg:col-span-8">
          <TrackMapLazy />
        </div>
      </div>
    </section>
  );
}
