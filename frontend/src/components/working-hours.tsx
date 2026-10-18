import { openingLines } from "@/lib/hours";
import type { BookingInfo } from "@/lib/types";

/** One line per schedule (the morning shift from the admin panel, then the evening hours), the same on every page. */
export function WorkingHours({ info }: { info: BookingInfo | null }) {
  return (
    <>
      {openingLines(info).map(({ label, text }) => (
        <span key={label} className="block">
          {label}: {text}
        </span>
      ))}
    </>
  );
}
