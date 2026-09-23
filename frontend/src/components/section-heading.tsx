import type { ReactNode } from "react";

type SectionHeadingProps = {
  eyebrow: string;
  title: string;
  lead?: ReactNode;
  /** Gold marks the customer-club section; everything else uses ink with a yellow rule. */
  tone?: "accent" | "gold";
  /** Page titles use h1 and a larger size; everything else is an h2. */
  as?: "h1" | "h2";
};

export function SectionHeading({ eyebrow, title, lead, tone = "accent", as: Heading = "h2" }: SectionHeadingProps) {
  const gold = tone === "gold";
  const sizeClass = Heading === "h1" ? "text-[clamp(2.5rem,7vw,5rem)]" : "text-[clamp(2rem,5vw,3.5rem)]";
  return (
    <div>
      <p className={`flex items-center gap-3 text-sm font-bold ${gold ? "text-gold" : "text-fg"}`}>
        <span aria-hidden="true" className={`h-[3px] w-8 rounded-full ${gold ? "bg-gold" : "bg-accent"}`} />
        {eyebrow}
      </p>
      <Heading className={`mt-5 font-black leading-[1.2] ${sizeClass}`}>{title}</Heading>
      {lead && <p className="mt-5 max-w-xl text-lg text-fg-muted">{lead}</p>}
    </div>
  );
}
