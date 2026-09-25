import type { ReactNode } from "react";

type SectionHeadingProps = {
  eyebrow: string;
  title: ReactNode;
  lead?: ReactNode;
  /** Page titles use h1 and a larger size; everything else is an h2. */
  as?: "h1" | "h2";
  /** On a carbon panel the lead switches to the light muted colour. */
  onCarbon?: boolean;
  align?: "start" | "center";
};

export function SectionHeading({ eyebrow, title, lead, as: Heading = "h2", onCarbon = false, align = "start" }: SectionHeadingProps) {
  const sizeClass = Heading === "h1" ? "text-[clamp(2.6rem,7vw,5.2rem)]" : "text-[clamp(2rem,5vw,3.6rem)]";
  return (
    <div className={align === "center" ? "mx-auto max-w-3xl text-center" : ""}>
      <p className="eyebrow">{eyebrow}</p>
      <Heading className={`mt-5 font-black leading-[1.15] ${sizeClass}`}>{title}</Heading>
      {lead && (
        <p className={`mt-5 max-w-xl text-lg ${align === "center" ? "mx-auto" : ""} ${onCarbon ? "text-on-carbon-muted" : "text-fg-muted"}`}>
          {lead}
        </p>
      )}
    </div>
  );
}
