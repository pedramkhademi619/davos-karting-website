import type { ReactNode } from "react";

const tones = {
  error: "border-signal/30 bg-signal-soft text-[#7a0600]",
  success: "border-go/30 bg-go-soft text-[#064d29]",
  info: "border-line-strong bg-surface-2 text-fg",
  warning: "border-accent bg-[#fff6d6] text-ink-soft",
} as const;

/** Inline message. Errors are announced immediately (role="alert"), everything else politely. */
export function Alert({ tone = "info", children, className = "" }: { tone?: keyof typeof tones; children: ReactNode; className?: string }) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`rounded-2xl border px-4 py-3 text-sm font-medium leading-7 ${tones[tone]} ${className}`}
    >
      {children}
    </div>
  );
}
