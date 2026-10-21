"use client";

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, TabHeader } from "@/components/admin/admin-ui";
import { DatePickerField } from "@/components/admin/date-picker-field";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { toLatinDigits, toman } from "@/lib/format";
import type { ScheduleSettings } from "@/lib/types";
import { PageSkeleton } from "@/components/ui/skeleton";

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
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    call<ScheduleSettings>("/settings/schedule")
      .then((result) => {
        if (cancelled) return;
        setSettings(result);
      })
      .catch((err) => !cancelled && setMessage({ tone: "error", text: errorMessage(err) }));
    return () => {
      cancelled = true;
    };
  }, [call]);

  if (!settings) return message ? <Alert tone="error">{message.text}</Alert> : <PageSkeleton variant="form" />;

  const set = <K extends keyof ScheduleSettings>(key: K, value: ScheduleSettings[K]) => setSettings({ ...settings, [key]: value });
  const num = (key: keyof ScheduleSettings) => (event: React.ChangeEvent<HTMLInputElement>) =>
    set(key, Number(toLatinDigits(event.target.value).replace(/[^\d]/g, "") || 0) as never);
  const setLimitMode = (mode: ScheduleSettings["daily_booking_limit_mode"]) =>
    setSettings({
      ...settings,
      daily_booking_limit_mode: mode,
      daily_people_limit: settings.daily_people_limit ?? 50,
      daily_ticket_limit: settings.daily_ticket_limit ?? 20,
    });
  const toggleDay = (key: "holiday_weekdays" | "closed_weekdays", day: number) =>
    set(key, settings[key].includes(day) ? settings[key].filter((d) => d !== day) : [...settings[key], day]);
  const toggleJuniorDay = (day: number) =>
    set("junior_weekdays", settings.junior_weekdays.includes(day) ? settings.junior_weekdays.filter((d) => d !== day) : [...settings.junior_weekdays, day]);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!settings) return;
    setBusy(true);
    setMessage(null);
    try {
      const saved = await call<ScheduleSettings>("/settings/schedule", {
        method: "PUT",
        body: settings,
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
          <p className="mt-5 text-sm leading-7 text-fg-muted">هر سانس تا قبل از شروع شیفتش آنلاین رزرو می‌شود؛ شیفت که شروع شد، همان شیفتِ همان روز آنلاین بسته می‌شود ولی شیفت‌های بعدی و روزهای بعد باز می‌مانند.</p>
        </Card>

        <Card title="شیفت‌ها و خودروها">
          <label className="flex items-center gap-3 font-bold">
            <input
              type="checkbox"
              className="h-5 w-5 accent-[#0c0d10]"
              checked={settings.morning_shift_enabled}
              onChange={(e) => set("morning_shift_enabled", e.target.checked)}
            />
            شیفت صبح داریم
          </label>
          {settings.morning_shift_enabled && (
            <div className="mt-4 grid grid-cols-2 gap-4 rounded-2xl bg-surface-2 p-4">
              <TimeField label="شیفت صبح: اولین سانس" value={settings.morning_start} onChange={(v) => set("morning_start", v)} />
              <TimeField label="شیفت صبح: پایان" value={settings.morning_end} onChange={(v) => set("morning_end", v)} />
            </div>
          )}
          <div className="mt-4 grid grid-cols-2 gap-4">
            <TimeField label="شیفت عصر: اولین سانس" value={settings.shift_start} onChange={(v) => set("shift_start", v)} />
            <TimeField label="شیفت عصر: پایان (بعد از نیمه‌شب هم مجاز)" value={settings.shift_end} onChange={(v) => set("shift_end", v)} />
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
            <p className="mt-2 text-xs leading-6 text-fg-subtle">
              برداشتن یک روز از این فهرست، همهٔ آن روزهای هفته را باز می‌کند. برای باز کردن فقط یک تاریخ مشخص از «روزهای باز استثنایی» پایین صفحه استفاده کنید.
            </p>
          </div>
        </Card>

        <Card title="ساعت حضور زیر ۱۵ سال">
          <p className="mb-4 text-sm leading-7 text-fg-muted">
            روزها و ساعتی که افراد زیر ۱۵ سال می‌توانند سوار شوند. جادوگر رزرو سایت و دستیار هوشمند همین را اعمال می‌کنند؛ سانس‌هایی که از
            ساعت شروع تا پیش از ساعت پایان شروع می‌شوند مجازند.
          </p>
          <DayChecks title="روزهای مجاز" selected={settings.junior_weekdays} onToggle={toggleJuniorDay} />
          <div className="mt-4 grid grid-cols-2 gap-4">
            <TimeField label="از ساعت" value={settings.junior_from} onChange={(v) => set("junior_from", v)} />
            <TimeField label="تا ساعت" value={settings.junior_until} onChange={(v) => set("junior_until", v)} />
          </div>
          <div className="mt-5 space-y-2" role="radiogroup" aria-label="این ساعت برای چه کسانی است">
            {(
              [
                { value: "drivers", label: "فقط نوجوان‌های ۱۱ تا ۱۴ ساله‌ای که خودشان تک‌نفره می‌رانند", hint: "کودکی که پشت بزرگسال روی صندلی عقب دونفره می‌نشیند، همه‌ی ساعت‌ها می‌تواند بیاید (قانون فعلی مجموعه)." },
                { value: "everyone", label: "همه‌ی افراد زیر ۱۵ سال، چه راننده و چه سرنشین صندلی عقب", hint: "خارج از این ساعت هیچ فرد زیر ۱۵ سالی سوار نمی‌شود." },
              ] as const
            ).map((option) => (
              <label key={option.value} className={`flex cursor-pointer items-start gap-3 rounded-2xl border-2 p-3 ${settings.junior_scope === option.value ? "border-ink" : "border-line"}`}>
                <input
                  type="radio"
                  name="junior-scope"
                  className="mt-1 h-4 w-4 accent-[#0c0d10]"
                  checked={settings.junior_scope === option.value}
                  onChange={() => set("junior_scope", option.value)}
                />
                <span>
                  <span className="block text-sm font-bold">{option.label}</span>
                  <span className="block text-xs leading-6 text-fg-subtle">{option.hint}</span>
                </span>
              </label>
            ))}
          </div>
        </Card>

        <Card title="محدودیت رزرو آنلاین در روز (برای مشتریان حضوری)">
          <p className="mb-4 text-sm leading-7 text-fg-muted">
            اگر همه‌چیز آنلاین رزرو شود، جایی برای مشتری حضوری نمی‌ماند. با این محدودیت، از یک تعداد مشخص به بعد در هر روز
            رزرو آنلاین بسته می‌شود؛ رزرو حضوری در پیست همچنان آزاد است.
          </p>
          <div className="flex flex-wrap gap-2" role="group" aria-label="نوع محدودیت">
            {(
              [
                { value: "none", label: "بدون محدودیت" },
                { value: "people", label: "بر اساس تعداد نفرات" },
                { value: "tickets", label: "بر اساس تعداد تیکت" },
                { value: "both", label: "ترکیبی (هرکدام زودتر رسید)" },
              ] as const
            ).map((opt) => (
              <button
                key={opt.value}
                type="button"
                aria-pressed={settings.daily_booking_limit_mode === opt.value}
                onClick={() => setLimitMode(opt.value)}
                className={`rounded-full border-2 px-4 py-2 text-sm font-bold transition-colors ${settings.daily_booking_limit_mode === opt.value ? "border-ink bg-ink text-accent" : "border-line-strong text-fg-muted hover:border-fg"}`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          {settings.daily_booking_limit_mode !== "none" && (
            <div className="mt-4 grid max-w-md grid-cols-2 gap-4">
              {(settings.daily_booking_limit_mode === "people" || settings.daily_booking_limit_mode === "both") && (
                <NumberField label="حداکثر نفر در روز" value={settings.daily_people_limit ?? 0} onChange={num("daily_people_limit")} />
              )}
              {(settings.daily_booking_limit_mode === "tickets" || settings.daily_booking_limit_mode === "both") && (
                <NumberField label="حداکثر تیکت در روز" value={settings.daily_ticket_limit ?? 0} onChange={num("daily_ticket_limit")} />
              )}
            </div>
          )}
          {settings.daily_booking_limit_mode === "both" && (
            <p className="mt-3 text-xs leading-6 text-fg-subtle">
              هر کدام از این دو سقف زودتر پر شود، رزرو آنلاین همان روز بسته می‌شود. مثلاً با ۵۰ نفر و ۲۰ تیکت، اگر ۲۰ تیکت ثبت شود
              (حتی با ۳۰ نفر) یا ۵۰ نفر پر شود (حتی با ۱۰ تیکت)، رزرو آنلاین بسته می‌شود.
            </p>
          )}
        </Card>

        <Card title="تعطیلات رسمی (قیمت تعطیل)">
          <DatePickerField value={settings.holiday_dates} onChange={(dates) => set("holiday_dates", dates)} />
        </Card>

        <Card title="روزهای بسته (بدون رزرو آنلاین)">
          <p className="mb-3 text-sm leading-7 text-fg-muted">فقط همین تاریخ‌ها بسته می‌شوند؛ روزهای دیگر هفته تغییر نمی‌کنند.</p>
          <DatePickerField
            value={settings.closed_dates}
            onChange={(dates) => setSettings({ ...settings, closed_dates: dates, open_dates: settings.open_dates.filter((d) => !dates.includes(d)) })}
          />
        </Card>

        <Card title="روزهای باز استثنایی (با وجود بسته بودن آن روز هفته)">
          <p className="mb-3 text-sm leading-7 text-fg-muted">
            برای باز کردن فقط یک پنجشنبه یا جمعه مشخص، همان تاریخ را اینجا انتخاب کنید؛ پنجشنبه‌های دیگر بسته می‌مانند. رزرو آنلاین فقط
            برای روزهای داخل بازهٔ «تا چند روز جلوتر» نمایش داده می‌شود.
          </p>
          <DatePickerField
            value={settings.open_dates}
            onChange={(dates) => setSettings({ ...settings, open_dates: dates, closed_dates: settings.closed_dates.filter((d) => !dates.includes(d)) })}
          />
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
