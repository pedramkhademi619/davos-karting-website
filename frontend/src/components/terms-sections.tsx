import { termsSections } from "@/content/terms";

/** The track's rules and privacy text, one panel per topic (anchors: #ages, #weather, #booking, #safety, #privacy). */
export function TermsSections() {
  return (
    <div className="space-y-5">
      {termsSections.map((section) => (
        <section key={section.id} id={section.id} className="panel scroll-mt-28 p-7 md:p-9">
          <h2 className="text-xl font-black md:text-2xl">{section.title}</h2>
          <ul className="mt-5 space-y-3.5">
            {section.points.map((point) => (
              <li key={point} className="flex gap-3 leading-8 text-fg-muted">
                <span aria-hidden="true" className="mt-3 h-2 w-2 shrink-0 rounded-full bg-accent" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
