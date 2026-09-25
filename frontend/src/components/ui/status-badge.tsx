import { RESERVATION_STATUS } from "@/lib/format";
import type { ReservationStatus } from "@/lib/types";

const tones = {
  go: "bg-go-soft text-[#064d29] ring-go/25",
  wait: "bg-[#fff3c4] text-ink-soft ring-accent/60",
  muted: "bg-surface-2 text-fg-muted ring-line-strong",
  stop: "bg-signal-soft text-[#7a0600] ring-signal/25",
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
