"use client";

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, TabHeader } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { fa, toLatinDigits, toman } from "@/lib/format";
import { isoToJalali, parseJalali } from "@/lib/jalali";
import type { ScheduleSettings } from "@/lib/types";

// Python weekday numbers (Monday = 0), in the order of the Iranian week.
const WEEK = [
  { value: 5, label: "شنبه" },
  { value: 6, label: "یکشنبه" },
  { value: 0, label: "دوشنبه" },
  { value: 1, label: "سه‌شنبه" },
  { value: 2, label: "چهارشنبه" },
  { value: 3, label: "پنجشنبه" },
  { value: 4, label: "جمعه" },
];

/** Booking settings and prices. Everything the site, the booking page and the AI assistant show comes from here. */
export function SettingsTab() {
  const { call, isOwner } = useAdmin();
  const [settings, setSettings] = useState<ScheduleSettings | null>(null);
  const [holidayText, setHolidayText] = useState("");
  const [closedText, setClosedText] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    call<ScheduleSettings>("/settings/schedule")
      .then((result) => {
        if (cancelled) return;
        setSettings(result);
        setHolidayText(result.holiday_dates.map(isoToJalali).join("\n"));
        setClosedText(result.closed_dates.map(isoToJalali).join("\n"));
      })
      .catch((err) => !cancelled && setMessage({ tone: "error", text: errorMessage(err) }));
    return () => {
      cancelled = true;
    };
  }, [call]);

  if (!settings) return message ? <Alert tone="error">{message.text}</Alert> : <Spinner className="h-8 w-8" />;

  const set = <K extends keyof ScheduleSettings>(key: K, value: ScheduleSettings[K]) => setSettings({ ...settings, [key]: value });
  const num = (key: keyof ScheduleSettings) => (event: React.ChangeEvent<HTMLInputElement>) =>
    set(key, Number(toLatinDigits(event.target.value).replace(/[^\d]/g, "") || 0) as never);
  const toggleDay = (key: "holiday_weekdays" | "closed_weekdays", day: number) =>
    set(key, settings[key].includes(day) ? settings[key].filter((d) => d !== day) : [...settings[key], day]);

  function parseDates(text: string): string[] | null {
    const lines = text.split(/[\n,،]+/).map((l) => l.trim()).filter(Boolean);
    const parsed = lines.map(parseJalali);
    return parsed.every((d): d is string => d !== null) ? parsed : null;
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!settings) return;
    const holidays = parseDates(holidayText);
    const closed = parseDates(closedText);
    if (!holidays || !closed) {
      setMessage({ tone: "error", text: "تاریخ‌ها را هر کدام در یک خط به شکل ۱۴۰۵/۰۷/۰۴ بنویسید." });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const saved = await call<ScheduleSettings>("/settings/schedule", {
        method: "PUT",
        body: { ...settings, holiday_dates: holidays, closed_dates: closed },
      });
      setSettings(saved);
      setMessage({ tone: "success", text: "ذخیره شد. سایت، صفحه رزرو و دستیار هوشمند از همین حالا (حداکثر ۳۰ ثانیه) با این تنظیمات کار می‌کنند." });
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save}>
      <TabHeader
        title="تنظیمات رزرو و قیمت‌ها"
        lead="قیمت‌ها، تعداد خودروها، ساعت سانس‌ها و روزهای بدون رزرو. سایت، صفحه رزرو و دستیار هوشمند همه از همین‌جا می‌خوانند."
        actions={
          isOwner && (
            <button type="submit" disabled={busy} className={buttonClasses("primary", "md")}>
              {busy ? <Spinner /> : "ذخیره تنظیمات"}
            </button>
          )
        }
      />
      {!isOwner && (
        <Alert tone="info" className="mb-6">
          فقط مالک می‌تواند تنظیمات را تغییر دهد.
        </Alert>
      )}
      {message && (
        <Alert tone={message.tone} className="mb-6">
          {message.text}
        </Alert>
      )}

      <fieldset disabled={!isOwner || busy} className="grid gap-6 lg:grid-cols-2">
        <Card title="رزرو آنلاین">
          <label className="flex items-center gap-3 font-bold">
            <input type="checkbox" className="h-5 w-5 accent-[#0c0d10]" checked={settings.online_booking_enabled} onChange={(e) => set("online_booking_enabled", e.target.checked)} />
            رزرو آنلاین باز است
          </label>
          <div className="mt-5 grid grid-cols-2 gap-4">
            <NumberField label="نگه‌داشتن برای پرداخت (دقیقه)" value={settings.hold_minutes} onChange={num("hold_minutes")} />
            <NumberField label="حداکثر خودرو در هر رزرو" value={settings.max_karts_per_reservation} onChange={num("max_karts_per_reservation")} />
            <NumberField label="رزرو از چند روز بعد (۰ = همان روز)" value={settings.min_days_ahead} onChange={num("min_days_ahead")} />
            <NumberField label="تا چند روز جلوتر" value={settings.max_days_ahead} onChange={num("max_days_ahead")} />
            <NumberField label="رزرو همان روز: حداقل دقیقه قبل از سانس" value={settings.same_day_lead_minutes} onChange={num("same_day_lead_minutes")} />
            <NumberField label="حداکثر رزرو پرداخت‌نشده هر مشتری" value={settings.max_active_holds_per_customer} onChange={num("max_active_holds_per_customer")} />
          </div>
        </Card>

        <Card title="سانس‌ها و خودروها">
          <div className="grid grid-cols-2 gap-4">
            <TimeField label="شروع اولین سانس" value={settings.shift_start} onChange={(v) => set("shift_start", v)} />
            <TimeField label="پایان سانس‌ها (بعد از نیمه‌شب هم مجاز)" value={settings.shift_end} onChange={(v) => set("shift_end", v)} />
            <NumberField label="فاصله سانس‌ها (دقیقه)" value={settings.interval_minutes} onChange={num("interval_minutes")} />
            <div />
            <NumberField label="تعداد خودروی تک‌نفره هر سانس" value={settings.single_capacity} onChange={num("single_capacity")} />
            <NumberField label="تعداد خودروی دونفره هر سانس" value={settings.double_capacity} onChange={num("double_capacity")} />
          </div>
        </Card>

        <Card title="قیمت‌ها (تومان)">
          <div className="grid grid-cols-2 gap-4">
            <NumberField label="تک‌نفره، روز عادی" value={settings.normal_single_toman} onChange={num("normal_single_toman")} hint={toman(settings.normal_single_toman)} />
            <NumberField label="دونفره، روز عادی" value={settings.normal_double_toman} onChange={num("normal_double_toman")} hint={toman(settings.normal_double_toman)} />
            <NumberField label="تک‌نفره، روز تعطیل" value={settings.holiday_single_toman} onChange={num("holiday_single_toman")} hint={toman(settings.holiday_single_toman)} />
            <NumberField label="دونفره، روز تعطیل" value={settings.holiday_double_toman} onChange={num("holiday_double_toman")} hint={toman(settings.holiday_double_toman)} />
          </div>
        </Card>

        <Card title="روزهای هفته">
          <DayChecks title="روزهای تعطیل (قیمت تعطیل)" selected={settings.holiday_weekdays} onToggle={(d) => toggleDay("holiday_weekdays", d)} />
          <div className="mt-5">
            <DayChecks title="روزهای بدون رزرو آنلاین" selected={settings.closed_weekdays} onToggle={(d) => toggleDay("closed_weekdays", d)} />
          </div>
        </Card>

        <Card title="تعطیلات رسمی (قیمت تعطیل)">
          <DatesField value={holidayText} onChange={setHolidayText} />
        </Card>

        <Card title="روزهای بسته (بدون رزرو آنلاین)">
          <DatesField value={closedText} onChange={setClosedText} />
        </Card>
      </fieldset>
    </form>
  );
}

function Labelled({ label, hint, children }: { label: string; hint?: ReactNode; children: ReactNode }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-fg-subtle">{hint}</span>}
    </label>
  );
}

function NumberField({ label, value, onChange, hint }: { label: string; value: number; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; hint?: ReactNode }) {
  return (
    <Labelled label={label} hint={hint}>
      <input className="field" dir="ltr" inputMode="numeric" value={String(value)} onChange={onChange} />
    </Labelled>
  );
}

function TimeField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <Labelled label={label}>
      <input className="field" type="time" dir="ltr" value={value} onChange={(e) => onChange(e.target.value)} />
    </Labelled>
  );
}

function DayChecks({ title, selected, onToggle }: { title: string; selected: number[]; onToggle: (day: number) => void }) {
  return (
    <div>
      <p className="label">{title}</p>
      <div className="flex flex-wrap gap-2">
        {WEEK.map((day) => {
          const on = selected.includes(day.value);
          return (
            <button
              key={day.value}
              type="button"
              aria-pressed={on}
              onClick={() => onToggle(day.value)}
              className={`rounded-full border-2 px-4 py-2 text-sm font-bold transition-colors ${on ? "border-ink bg-ink text-accent" : "border-line-strong text-fg-muted hover:border-fg"}`}
            >
              {day.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function DatesField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const count = value.split(/\n/).filter((l) => l.trim()).length;
  return (
    <Labelled label="هر تاریخ در یک خط (شمسی، مثل ۱۴۰۵/۰۷/۰۴)" hint={`${fa(count)} تاریخ`}>
      <textarea className="field font-mono" dir="ltr" rows={6} value={value} onChange={(e) => onChange(e.target.value)} />
    </Labelled>
  );
}
