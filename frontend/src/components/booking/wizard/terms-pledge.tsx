import { pledgePoints } from "@/content/terms";
import { hrefFor } from "@/lib/urls";

/** The weather rule in one line, shown while the day is being chosen: it is the thing people forget to check. */
export function WeatherNote() {
  return (
    <p className="mb-4 rounded-2xl bg-accent/15 px-4 py-3 text-sm font-bold leading-7 ring-1 ring-accent/40">
      پیست روباز است: با بارندگی یا بدی هوا تعطیل می‌شود و پولی برگردانده نمی‌شود، فقط رزرو به روز دیگر منتقل می‌شود. پیش از رزرو آب‌وهوا را
      بررسی کنید.
    </p>
  );
}

/** What the customer commits to before the karts are held: the ages are right, the weather rule, the rules read. */
export function TermsPledge({ accepted, onChange }: { accepted: boolean; onChange: (accepted: boolean) => void }) {
  return (
    <div className="rounded-[1.6rem] border border-line-strong bg-surface p-5">
      <h3 className="text-base font-black">پیش از ثبت، بخوانید و تأیید کنید</h3>
      <ul className="mt-3 space-y-2 text-sm leading-7 text-fg-muted">
        {pledgePoints.map((point) => (
          <li key={point} className="flex gap-2.5">
            <span aria-hidden="true" className="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
            <span>{point}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-sm">
        <a href={hrefFor("/terms", true)} target="_blank" rel="noopener noreferrer" className="font-bold underline underline-offset-4 decoration-accent decoration-2">
          متن کامل قوانین و حریم خصوصی
        </a>
      </p>
      <label className="mt-4 flex cursor-pointer items-start gap-3 rounded-2xl bg-surface-2 p-4 font-bold leading-7">
        <input
          type="checkbox"
          checked={accepted}
          onChange={(event) => onChange(event.target.checked)}
          className="mt-1.5 h-5 w-5 shrink-0 accent-[var(--color-accent)]"
        />
        <span>سن و قد همه را درست وارد کرده‌ام و موارد بالا را خوانده و می‌پذیرم.</span>
      </label>
    </div>
  );
}
