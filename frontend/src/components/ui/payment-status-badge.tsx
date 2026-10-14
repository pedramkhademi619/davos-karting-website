import { PAYMENT_STATUS } from "@/lib/format";
import type { PaymentStatusValue } from "@/lib/types";

const tones: Record<PaymentStatusValue, string> = {
  paid: "bg-go-soft text-[#064d29] ring-go/25",
  failed: "bg-signal-soft text-[#7a0600] ring-signal/25",
  expired: "bg-surface-2 text-fg-muted ring-line-strong",
  reversed: "bg-surface-2 text-fg-muted ring-line-strong",
  created: "bg-[#fff3c4] text-ink-soft ring-accent/60",
  redirected: "bg-[#fff3c4] text-ink-soft ring-accent/60",
  verifying: "bg-[#fff3c4] text-ink-soft ring-accent/60",
  unknown: "bg-[#fff3c4] text-ink-soft ring-accent/60",
  refund_pending: "bg-[#fff3c4] text-ink-soft ring-accent/60",
};

export function PaymentStatusBadge({ status }: { status: PaymentStatusValue }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ring-1 ${tones[status] ?? tones.expired}`}>
      <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
      {PAYMENT_STATUS[status] ?? status}
    </span>
  );
}
