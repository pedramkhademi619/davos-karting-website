"use client";

import type { ReactNode } from "react";
import { MinusIcon, PlusIcon } from "@/components/icons";
import { fa } from "@/lib/format";
import { dayRange, type Crew, type JuniorWindow, type KartPlan } from "@/components/booking/wizard/crew";

type Group = { key: keyof Crew; title: string; hint: string; badge: string; colour: string };

const GROUPS: Group[] = [
  { key: "licensed", title: "بزرگسال با گواهینامه", hint: "۱۸ سال به بالا؛ تک‌نفره یا راننده‌ی دونفره", badge: "18+", colour: "#ffc400" },
  { key: "adult", title: "بالای ۱۶ سال", hint: "بدون گواهینامه یا ۱۶–۱۷ ساله؛ تک‌نفره", badge: "16+", colour: "#ff6a3d" },
  { key: "teen", title: "نوجوان ۱۱ تا ۱۴ سال", hint: "با قد بیشتر از ۱۴۰ سانتی‌متر", badge: "11–14", colour: "#4e92ff" },
  { key: "kid", title: "کودک ۴ تا ۱۵ سال", hint: "روی صندلی عقب دونفره، پشت یک بزرگسال", badge: "4–15", colour: "#1ee07a" },
];

/** A helmet, tinted per group: the crew is drawn as a row of helmets. */
export function Helmet({ colour, className = "" }: { colour: string; className?: string }) {
  return (
    <svg viewBox="0 0 40 36" className={className} aria-hidden="true">
      <path d="M4 22C4 11 12 3 22 3s15 7 15 15v6c0 2-1.5 3.5-3.5 3.5H17L9 33H6c-1.2 0-2-.9-2-2V22z" fill={colour} />
      <path d="M17 14h17.5c1 0 1.7.9 1.4 1.9l-1.4 5.1H17c-1.7 0-3-1.3-3-3v-1c0-1.7 1.3-3 3-3z" fill="#0b0c0f" opacity=".85" />
      <path d="M20 15.5h12" stroke="#fff" strokeOpacity=".35" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M8 18c1.5-6 6-10 12-11" stroke="#fff" strokeOpacity=".35" strokeWidth="2" strokeLinecap="round" fill="none" />
    </svg>
  );
}

type CrewStepProps = {
  crew: Crew;
  onCrew: (crew: Crew) => void;
  teensDrive: boolean;
  onTeensDrive: (value: boolean) => void;
  plan: KartPlan;
  manual: boolean;
  onManual: (value: boolean) => void;
  manualSingles: number;
  manualDoubles: number;
  juniorWindow: JuniorWindow;
  onManualSingles: (value: number) => void;
  onManualDoubles: (value: number) => void;
  maxKarts: number;
};

/** Step 1: who is coming. The kart mix follows from the riding rules and is shown live as a little grid of karts. */
export function CrewStep(props: CrewStepProps) {
  const { crew, plan } = props;
  const set = (key: keyof Crew, value: number) => props.onCrew({ ...crew, [key]: Math.max(0, Math.min(20, value)) });

  if (props.manual) {
    return (
      <div className="space-y-4">
        <Counter
          title="خودروی تک‌نفره"
          hint="از ۱۶ سال؛ ۱۱ تا ۱۴ سال با شرط قد و ساعت"
          value={props.manualSingles}
          onChange={props.onManualSingles}
          max={props.maxKarts}
          badge={<span className="race-number text-xs font-black text-accent">1×</span>}
        />
        <Counter
          title="خودروی دونفره"
          hint="راننده ۱۸+ با گواهینامه، پشتش کودک ۴ تا ۱۵ سال"
          value={props.manualDoubles}
          onChange={props.onManualDoubles}
          max={props.maxKarts}
          badge={<span className="race-number text-xs font-black text-accent">2×</span>}
        />
        <button type="button" onClick={() => props.onManual(false)} className="text-sm font-bold text-fg-muted underline underline-offset-4 hover:text-fg">
          بگذار جادوگر از روی افراد حساب کند
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {GROUPS.map((group) => (
          <Counter
            key={group.key}
            title={group.title}
            hint={group.hint}
            value={crew[group.key]}
            onChange={(value) => set(group.key, value)}
            max={20}
            badge={<Helmet colour={group.colour} className="h-7 w-8 sm:h-8 sm:w-9" />}
            tag={group.badge}
          />
        ))}
      </div>

      {crew.teen > 0 && (
        <fieldset className="space-y-2.5">
          <legend className="mb-2.5 font-black">نوجوان‌های ۱۱ تا ۱۴ سال چطور سوار شوند؟</legend>
          <TeenChoice
            checked={props.teensDrive}
            onSelect={() => props.onTeensDrive(true)}
            title="خودشان رانندگی کنند"
            text={`با خودروی تک‌نفره؛ فقط ${dayRange(props.juniorWindow.days)} و فقط در سانس‌های ساعت ${fa(props.juniorWindow.from)} تا ${fa(props.juniorWindow.until)}.`}
          />
          <TeenChoice
            checked={!props.teensDrive}
            onSelect={() => props.onTeensDrive(false)}
            title="پشت یک بزرگسال بنشینند"
            text={
              props.juniorWindow.everyone
                ? "روی صندلی عقب خودروی دونفره؛ برای هر نوجوان یک بزرگسال با گواهینامه لازم است. ساعت حضور زیر ۱۵ سال همچنان برقرار است."
                : "روی صندلی عقب خودروی دونفره؛ همه‌ی روزها و همه‌ی ساعت‌ها. برای هر نوجوان یک بزرگسال با گواهینامه لازم است."
            }
          />
        </fieldset>
      )}

      <KartGarage plan={plan} />

      <button type="button" onClick={() => props.onManual(true)} className="text-sm font-bold text-fg-muted underline underline-offset-4 hover:text-fg">
        خودم تعداد خودروها را انتخاب می‌کنم
      </button>
    </div>
  );
}

/** One of the two ways a teen can ride, as a radio card. */
function TeenChoice({ checked, onSelect, title, text }: { checked: boolean; onSelect: () => void; title: string; text: string }) {
  return (
    <label
      className={`flex cursor-pointer items-start gap-3 rounded-2xl border p-3.5 transition-colors sm:p-4 ${
        checked ? "border-accent bg-accent/[0.08]" : "border-white/10 bg-white/[0.025] hover:border-white/25"
      }`}
    >
      <input type="radio" name="teens-ride" checked={checked} onChange={onSelect} className="peer sr-only" />
      <span
        aria-hidden="true"
        className={`mt-1 grid h-5 w-5 shrink-0 place-items-center rounded-full border-2 peer-focus-visible:ring-2 peer-focus-visible:ring-accent ${
          checked ? "border-accent" : "border-white/30"
        }`}
      >
        {checked && <span className="h-2.5 w-2.5 rounded-full bg-accent" />}
      </span>
      <span>
        <span className="block font-black">{title}</span>
        <span className="mt-1 block text-sm leading-6 text-fg-muted">{text}</span>
      </span>
    </label>
  );
}

/** The karts the crew needs, drawn in the garage: one bay per kart, a passenger seat on the doubles. */
function KartGarage({ plan }: { plan: KartPlan }) {
  const bays = [...Array(plan.singles).fill("single"), ...Array(plan.doubles).fill("double")] as ("single" | "double")[];
  return (
    <div className={`rounded-3xl border p-4 transition-colors ${plan.ok ? "border-accent/40 bg-accent/[0.06]" : "border-signal/40 bg-signal/[0.08]"}`} aria-live="polite">
      <div className="flex items-center justify-between gap-3">
        <p className="font-black">{plan.ok ? "خودروهای پیشنهادی" : "این ترکیب ممکن نیست"}</p>
        {plan.ok && (
          <p className="text-sm font-bold text-accent">
            {plan.singles > 0 && `${fa(plan.singles)} تک‌نفره`}
            {plan.singles > 0 && plan.doubles > 0 && " + "}
            {plan.doubles > 0 && `${fa(plan.doubles)} دونفره`}
          </p>
        )}
      </div>
      {!plan.ok && <p className="mt-2 text-sm leading-7 text-fg-muted">{plan.reason}</p>}
      {bays.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2" aria-hidden="true">
          {bays.map((kind, index) => (
            <span
              key={index}
              className="pop grid h-14 place-items-center rounded-2xl border border-white/10 bg-black/40 px-3"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <KartGlyph double={kind === "double"} />
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/** A kart from above; a double has a second (passenger) seat. */
export function KartGlyph({ double = false, className = "h-9 w-12" }: { double?: boolean; className?: string }) {
  return (
    <svg viewBox="0 0 48 32" className={className}>
      <rect x="6" y="3" width="8" height="6" rx="2" fill="#2b2e35" />
      <rect x="6" y="23" width="8" height="6" rx="2" fill="#2b2e35" />
      <rect x="34" y="3" width="8" height="6" rx="2" fill="#2b2e35" />
      <rect x="34" y="23" width="8" height="6" rx="2" fill="#2b2e35" />
      <path d="M4 12c0-2 2-4 4-4h30c4 0 8 3.5 8 8s-4 8-8 8H8c-2 0-4-2-4-4z" fill="#ffc400" />
      <circle cx={double ? 26 : 22} cy="16" r="4.5" fill="#0b0c0f" />
      {double && <circle cx="15" cy="16" r="3.6" fill="#0b0c0f" opacity=".8" />}
      <rect x="40" y="13" width="4" height="6" rx="1.5" fill="#0b0c0f" opacity=".6" />
    </svg>
  );
}

function Counter({
  title,
  hint,
  value,
  onChange,
  max,
  badge,
  tag,
}: {
  title: string;
  hint: string;
  value: number;
  onChange: (value: number) => void;
  max: number;
  badge: ReactNode;
  tag?: string;
}) {
  return (
    <div className={`flex items-center gap-2.5 rounded-2xl border p-2.5 transition-colors sm:gap-3 sm:p-4 ${value > 0 ? "border-accent/50 bg-white/[0.05]" : "border-white/10 bg-white/[0.025]"}`}>
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-black/40 sm:h-12 sm:w-12">{badge}</span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2">
          <span className="text-[0.95rem] font-black leading-6 sm:text-base">{title}</span>
          {tag && (
            <span dir="ltr" className="race-number hidden rounded-md bg-white/10 px-1.5 py-0.5 text-[0.62rem] font-bold text-fg-muted sm:inline">
              {tag}
            </span>
          )}
        </span>
        <span className="block text-[0.72rem] leading-5 text-fg-muted sm:text-sm">{hint}</span>
      </span>
      <span className="flex shrink-0 items-center gap-1 sm:gap-1.5">
        <button
          type="button"
          onClick={() => onChange(value - 1)}
          disabled={value <= 0}
          aria-label={`کم کردن ${title}`}
          className="grid h-9 w-9 place-items-center rounded-full border border-white/15 transition active:scale-90 disabled:opacity-30 sm:h-10 sm:w-10"
        >
          <MinusIcon className="h-4 w-4" />
        </button>
        <span className="w-6 text-center text-xl font-black sm:w-7" aria-live="polite" aria-label={`${title}: ${fa(value)}`}>
          {fa(value)}
        </span>
        <button
          type="button"
          onClick={() => onChange(value + 1)}
          disabled={value >= max}
          aria-label={`اضافه کردن ${title}`}
          className="grid h-9 w-9 place-items-center rounded-full bg-accent text-ink transition active:scale-90 disabled:opacity-30 sm:h-10 sm:w-10"
        >
          <PlusIcon className="h-4 w-4" />
        </button>
      </span>
    </div>
  );
}
