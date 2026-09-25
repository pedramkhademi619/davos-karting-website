import { site } from "@/content/site";

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true" focusable="false">
      <rect width="40" height="40" rx="11" fill="var(--color-accent)" />
      <path
        fill="var(--color-ink)"
        fillRule="evenodd"
        d="M12 10h8.4c6.3 0 9.6 3.6 9.6 10s-3.3 10-9.6 10H12V10zm5 5v10h3.2c3 0 4.6-1.9 4.6-5s-1.6-5-4.6-5H17z"
      />
      <path fill="var(--color-ink)" d="M6 27.5l7-2.2v3.2l-7 2.2z" />
    </svg>
  );
}

/** Wordmark; `tone="light"` is for carbon panels. */
export function Logo({ tone = "dark" }: { tone?: "dark" | "light" }) {
  return (
    <span className="inline-flex items-center gap-3">
      <LogoMark className="h-10 w-10 shrink-0" />
      <span className="flex flex-col gap-1.5 leading-none">
        <span className={`text-[1.1rem] font-black ${tone === "light" ? "text-on-carbon" : "text-fg"}`}>{site.name}</span>
        <span
          dir="ltr"
          className={`hidden font-display text-[0.6rem] font-medium uppercase tracking-[0.34em] sm:block ${
            tone === "light" ? "text-on-carbon-muted" : "text-fg-muted"
          }`}
        >
          {site.nameLatin}
        </span>
      </span>
    </span>
  );
}
