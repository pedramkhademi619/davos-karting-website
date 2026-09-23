import { BoltIcon, FlagIcon, TargetIcon } from "@/components/icons";
import { SectionHeading } from "@/components/section-heading";
import { experience } from "@/content/site";

const icons = { bolt: BoltIcon, target: TargetIcon, flag: FlagIcon } as const;

export function Experience() {
  return (
    <section className="container-page py-24 md:py-36">
      <div className="grid gap-14 lg:grid-cols-12 lg:gap-20">
        <div className="lg:col-span-5">
          <div className="lg:sticky lg:top-32">
            <SectionHeading
              eyebrow="تجربه داوس"
              title="پشت فرمان، سه چیز مهم است"
              lead="کارتینگ ترکیبی از سرعت، دقت و رقابت است و هر سه را از همان دور اول حس می‌کنید."
            />
          </div>
        </div>

        <ol className="divide-y divide-line border-y border-line lg:col-span-7">
          {experience.map((item) => {
            const IconComponent = icons[item.icon];
            return (
              <li key={item.index} className="group grid grid-cols-[auto_1fr_auto] items-start gap-6 py-10 md:gap-10 md:py-14">
                <span className="text-2xl font-black text-fg-subtle transition-colors duration-300 group-hover:text-fg">{item.index}</span>
                <div>
                  <h3 className="text-3xl font-black">{item.title}</h3>
                  <p className="mt-4 max-w-md text-fg-muted">{item.text}</p>
                </div>
                <span className="grid h-14 w-14 place-items-center rounded-full border border-line-strong bg-surface text-fg transition-all duration-300 group-hover:-translate-y-1 group-hover:border-accent group-hover:bg-accent">
                  <IconComponent className="h-7 w-7" />
                </span>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
