import type { ComponentType, ReactNode, SVGProps } from "react";

type InfoCardProps = {
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  label: string;
  children: ReactNode;
};

export function InfoCard({ icon: IconComponent, label, children }: InfoCardProps) {
  return (
    <div className="rounded-3xl border border-line bg-surface p-7 shadow-[0_1px_0_rgb(17_17_20/0.03),0_26px_50px_-30px_rgb(90_65_10/0.3)] transition-all duration-300 hover:-translate-y-0.5 hover:border-line-strong">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-accent text-ink">
        <IconComponent className="h-6 w-6" />
      </span>
      <h3 className="mt-6 text-sm font-bold text-fg-muted">{label}</h3>
      <div className="mt-2 text-lg font-bold text-fg">{children}</div>
    </div>
  );
}
