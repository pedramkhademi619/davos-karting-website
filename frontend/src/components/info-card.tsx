import type { ComponentType, ReactNode, SVGProps } from "react";

type InfoCardProps = {
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  label: string;
  children: ReactNode;
  /** h3 under a section heading (default), h2 when the cards sit right under the page's h1. */
  headingLevel?: 2 | 3;
};

export function InfoCard({ icon: IconComponent, label, children, headingLevel = 3 }: InfoCardProps) {
  const Label = headingLevel === 2 ? "h2" : "h3";
  return (
    <div className="panel group p-7 transition-transform duration-500 ease-out-expo hover:-translate-y-1">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-ink text-accent transition-transform duration-500 ease-snap group-hover:rotate-[-8deg]">
        <IconComponent className="h-6 w-6" />
      </span>
      <Label className="mt-6 text-sm font-bold text-fg-muted">{label}</Label>
      <div className="mt-2 text-lg font-bold text-fg">{children}</div>
    </div>
  );
}
