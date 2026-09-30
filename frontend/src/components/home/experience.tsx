import { BoltIcon, FlagIcon, TargetIcon } from "@/components/icons";
import { SectionHeading } from "@/components/section-heading";
import { experience } from "@/content/site";

const icons = { bolt: BoltIcon, target: TargetIcon, flag: FlagIcon } as const;

export function Experience() {
  return (
    <section className="container-page py-24 md:py-32">
      <SectionHeading
        eyebrow="تجربه داوس"
        title={
          <>
            پشت فرمان، <span className="marker">سه چیز</span> مهم است
          </>
        }
        lead="کارتینگ ترکیبی از سرعت، دقت و رقابت است و هر سه را از همان دور اول حس می‌کنید."
      />

      <ol className="mt-14 grid gap-5 md:grid-cols-3">
        {experience.map((item) => {
          const IconComponent = icons[item.icon];
          return (
            <li
              key={item.index}
              className="reveal panel group relative overflow-hidden p-8 transition-transform duration-500 ease-out-expo hover:-translate-y-1.5 md:p-10"
            >
              <span
                aria-hidden="true"
                className="race-number pointer-events-none absolute left-5 top-4 text-[5.5rem] font-black leading-none text-transparent [-webkit-text-stroke:1.5px_var(--color-line-strong)] transition-colors duration-500 group-hover:[-webkit-text-stroke-color:var(--color-accent)]"
                dir="ltr"
              >
                {item.index}
              </span>
              <span className="relative grid h-14 w-14 place-items-center rounded-2xl bg-ink text-accent transition-transform duration-500 ease-snap group-hover:rotate-[-8deg] group-hover:scale-110">
                <IconComponent className="h-7 w-7" />
              </span>
              <h3 className="relative mt-8 text-3xl font-black">{item.title}</h3>
              <p className="relative mt-4 text-fg-muted">{item.text}</p>
              <span
                aria-hidden="true"
                className="absolute inset-x-0 bottom-0 h-1.5 origin-right scale-x-0 bg-accent transition-transform duration-500 ease-out-expo group-hover:scale-x-100"
              />
            </li>
          );
        })}
      </ol>
    </section>
  );
}
