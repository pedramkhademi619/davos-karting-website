import type { ReactNode } from "react";
import { SectionHeading } from "@/components/section-heading";
import { SpeedLines } from "@/components/speed-lines";
import { stagger } from "@/lib/stagger";

type PageHeroProps = {
  eyebrow: string;
  title: ReactNode;
  lead?: ReactNode;
  children?: ReactNode;
};

/** The inner pages' header: a carbon cockpit band with speed lines, closed by the checkered finish-line edge. */
export function PageHero({ eyebrow, title, lead, children }: PageHeroProps) {
  return (
    <section className="carbon relative isolate overflow-hidden">
      <SpeedLines />
      <div className="container-page relative py-16 md:py-24">
        <div className="rise" style={stagger(0)}>
          <SectionHeading as="h1" eyebrow={eyebrow} title={title} lead={lead} onCarbon />
        </div>
        {children && (
          <div className="rise mt-8" style={stagger(1)}>
            {children}
          </div>
        )}
      </div>
      <div className="checker" aria-hidden="true" />
    </section>
  );
}
