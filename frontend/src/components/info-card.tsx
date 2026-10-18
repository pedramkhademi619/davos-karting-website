import type { ComponentType, ReactNode, SVGProps } from "react";

type InfoCardProps = {
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  label: string;
  children: ReactNode;
};

export function InfoCard({ icon: IconComponent, label, children }: InfoCardProps) {
  return (
    <div className="panel group p-7 transition-transform duration-500 ease-out-expo hover:-translate-y-1">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-ink text-accent transition-transform duration-500 ease-snap group-hover:rotate-[-8deg]">
        <IconComponent className="h-6 w-6" />
      </span>
      <h3 className="mt-6 text-sm font-bold text-fg-muted">{label}</h3>
      <div className="mt-2 text-lg font-bold text-fg">{children}</div>
    </div>
  );
}
