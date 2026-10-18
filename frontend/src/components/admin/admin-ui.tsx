import type { ReactNode } from "react";

/** Shared building blocks of the admin screens. */

export function TabHeader({ title, lead, actions }: { title: string; lead?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-3xl font-black md:text-4xl">{title}</h1>
        {lead && <p className="mt-2 max-w-2xl text-fg-muted">{lead}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
    </div>
  );
}

export function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`panel p-5 md:p-6 ${className}`}>
      {title && <h2 className="mb-5 text-lg font-black">{title}</h2>}
      {children}
    </section>
  );
}

export function Kpi({ label, value, note, tone = "default" }: { label: string; value: ReactNode; note?: ReactNode; tone?: "default" | "accent" | "dark" }) {
  const toneClass =
    tone === "accent" ? "bg-accent text-ink" : tone === "dark" ? "carbon" : "bg-surface outline outline-1 outline-line";
  return (
    <div className={`rounded-3xl p-5 ${toneClass}`}>
      <p className={`text-sm font-bold ${tone === "dark" ? "text-on-carbon-muted" : tone === "accent" ? "text-ink-soft" : "text-fg-muted"}`}>
        {label}
      </p>
      <p className="mt-3 text-3xl font-black leading-none">{value}</p>
      {note && <p className={`mt-2 text-xs ${tone === "dark" ? "text-on-carbon-muted" : "text-fg-subtle"}`}>{note}</p>}
    </div>
  );
}

/** A horizontally scrollable table with the admin styling; `head` are the column titles. */
export function Table({ head, children, empty }: { head: string[]; children: ReactNode; empty?: boolean }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
      <table className="w-full min-w-[40rem] border-collapse text-sm">
        <thead>
          <tr className="border-b border-line bg-surface-2 text-right text-xs text-fg-muted">
            {head.map((title) => (
              <th key={title} scope="col" className="whitespace-nowrap px-4 py-3 font-bold">
                {title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">{children}</tbody>
      </table>
      {empty && <p className="p-8 text-center text-fg-muted">موردی پیدا نشد.</p>}
    </div>
  );
}

export const cell = "whitespace-nowrap px-4 py-3 align-middle";

export function Pager({ offset, limit, total, onChange }: { offset: number; limit: number; total: number; onChange: (offset: number) => void }) {
  if (total <= limit) return null;
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.ceil(total / limit);
  return (
    <div className="mt-4 flex items-center justify-center gap-3 text-sm">
      <button type="button" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))} className="rounded-full border border-line-strong px-4 py-2 font-bold disabled:opacity-40">
        قبلی
      </button>
      <span className="text-fg-muted">
        صفحه {page.toLocaleString("fa-IR")} از {pages.toLocaleString("fa-IR")}
      </span>
      <button type="button" disabled={offset + limit >= total} onClick={() => onChange(offset + limit)} className="rounded-full border border-line-strong px-4 py-2 font-bold disabled:opacity-40">
        بعدی
      </button>
    </div>
  );
}
