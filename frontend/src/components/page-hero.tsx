import type { ReactNode } from "react";
import { SectionHeading } from "@/components/section-heading";
import { stagger } from "@/lib/stagger";

type PageHeroProps = {
  eyebrow: string;
  title: string;
  lead?: ReactNode;
};

/** Compact, atmospheric header shared by the inner pages, closed by the checkered finish-line edge. */
export function PageHero({ eyebrow, title, lead }: PageHeroProps) {
  return (
    <section className="relative isolate overflow-hidden">
      <div className="hero-bg" aria-hidden="true" />
      <div className="grain" aria-hidden="true" />
      <div className="container-page py-20 md:py-28">
        <div className="rise" style={stagger(0)}>
          <SectionHeading as="h1" eyebrow={eyebrow} title={title} lead={lead} />
        </div>
      </div>
      <div className="checker" aria-hidden="true" />
    </section>
  );
}
