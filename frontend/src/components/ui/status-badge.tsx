import { RESERVATION_STATUS } from "@/lib/format";
import type { ReservationStatus } from "@/lib/types";

const tones = {
  go: "bg-go-soft text-go-text ring-go/25",
  wait: "bg-wait-soft text-wait-text ring-accent/60",
  muted: "bg-surface-2 text-fg-muted ring-line-strong",
  stop: "bg-signal-soft text-signal-text ring-signal/25",
} as const;

export function StatusBadge({ status }: { status: ReservationStatus }) {
  const { label, tone } = RESERVATION_STATUS[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ring-1 ${tones[tone]}`}>
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}
