"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card } from "@/components/admin/admin-ui";
import { SingleDatePicker } from "@/components/admin/date-picker-field";
import { Field } from "@/components/admin/accounting/accounting-fields";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import type { AccountingSettings } from "@/lib/accounting";
import { fa, toLatinDigits } from "@/lib/format";
import { currentBusinessDay, isoToJalali, isoToJalaliParts } from "@/lib/jalali";

/** How tickets are booked (VAT, gateway fee, when revenue counts), the period lock, year-end and re-syncing old sales. */
export function AccountingSettingsView({ onChanged }: { onChanged: () => void }) {
  const { call } = useAdmin();
  const [settings, setSettings] = useState<AccountingSettings | null>(null);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const today = currentBusinessDay();
  const [from, setFrom] = useState(today);
  const [to, setTo] = useState(today);
  const [closeYear, setCloseYear] = useState(isoToJalaliParts(today).jy - 1);

  useEffect(() => {
    let cancelled = false;
    call<AccountingSettings>("/accounting/settings")
      .then((s) => !cancelled && setSettings(s))
      .catch((err) => !cancelled && setMessage({ tone: "error", text: errorMessage(err) }));
    return () => {
      cancelled = true;
    };
  }, [call]);

  if (!settings) return message ? <Alert tone="error">{message.text}</Alert> : <Spinner className="h-8 w-8" />;

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!settings) return;
    setBusy(true);
    setMessage(null);
    try {
      setSettings(await call<AccountingSettings>("/accounting/settings", { method: "PUT", body: settings }));
      setMessage({ tone: "success", text: "ذخیره شد." });
      onChanged();
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  async function sync() {
    setBusy(true);
    setMessage(null);
    try {
      const result = await call<{ sales_booked: number; revenue_recognized: number }>("/accounting/sync", { method: "POST", body: { date_from: from, date_to: to } });
      setMessage({ tone: "success", text: `${fa(result.sales_booked)} فروش ثبت و درآمد ${fa(result.revenue_recognized)} بلیت شناسایی شد.` });
      onChanged();
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  async function closeFiscalYear() {
    if (!window.confirm(`سال ${fa(closeYear)} بسته شود؟ حساب‌های درآمد و هزینه آن به سود انباشته منتقل و سال قفل می‌شود.`)) return;
    setBusy(true);
    setMessage(null);
    try {
      await call(`/accounting/fiscal-years/${closeYear}/close`, { method: "POST" });
      setMessage({ tone: "success", text: `سال ${fa(closeYear)} بسته شد.` });
      setSettings(await call<AccountingSettings>("/accounting/settings"));
      onChanged();
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      <Card title="شیوه ثبت فروش">
        <form onSubmit={save} className="grid max-w-3xl gap-5 sm:grid-cols-2">
          <label className="flex items-center gap-3 font-bold sm:col-span-2">
            <input type="checkbox" className="h-5 w-5 accent-[#0c0d10]" checked={settings.auto_posting_enabled} onChange={(e) => setSettings({ ...settings, auto_posting_enabled: e.target.checked })} />
            فروش آنلاین و حضوری خودکار در دفاتر ثبت شود
          </label>
          <Field label="درصد مالیات بر ارزش افزوده" hint="۰ یعنی مجموعه مشمول نیست. مالیات از داخل قیمت بلیت جدا می‌شود، روی آن اضافه نمی‌شود.">
            <input className="field" dir="ltr" value={fa(settings.vat_percent)} onChange={(e) => setSettings({ ...settings, vat_percent: Math.min(30, Number(toLatinDigits(e.target.value).replace(/\D/g, "")) || 0) })} />
          </Field>
          <Field label="کارمزد درگاه پرداخت (درصد)" hint="مثلا ۱ یا ۱.۵؛ از هر پرداخت آنلاین به‌عنوان هزینه کم می‌شود.">
            <input className="field" dir="ltr" value={settings.gateway_fee_percent} onChange={(e) => setSettings({ ...settings, gateway_fee_percent: Math.min(10, Number(toLatinDigits(e.target.value).replace(/[^\d.]/g, "")) || 0) })} />
          </Field>
          <div className="sm:col-span-2">
            <p className="label">درآمد بلیت چه زمانی حساب شود؟</p>
            <div className="flex flex-wrap gap-2">
              {(
                [
                  { value: "on_payment", label: "روز پرداخت (ساده)" },
                  { value: "on_session", label: "روز سانس (بلیت تا زمان سانس «پیش‌دریافت از مشتری» است)" },
                ] as const
              ).map((o) => (
                <button
                  key={o.value}
                  type="button"
                  aria-pressed={settings.revenue_recognition === o.value}
                  onClick={() => setSettings({ ...settings, revenue_recognition: o.value })}
                  className={`rounded-full border-2 px-4 py-2 text-sm font-bold ${settings.revenue_recognition === o.value ? "border-ink bg-ink text-accent" : "border-line-strong text-fg-muted hover:border-fg"}`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>
          <div className="sm:col-span-2">
            <Field label="قفل دوره: تا این تاریخ سندی ثبت یا ابطال نمی‌شود" hint={settings.locked_through ? `قفل تا ${fa(isoToJalali(settings.locked_through))}` : "بدون قفل"}>
              <div className="flex flex-wrap items-center gap-3">
                <SingleDatePicker value={settings.locked_through ?? today} onChange={(iso) => setSettings({ ...settings, locked_through: iso })} label="قفل تا" />
                {settings.locked_through && (
                  <button type="button" className="text-sm font-bold underline underline-offset-4" onClick={() => setSettings({ ...settings, locked_through: null })}>
                    برداشتن قفل
                  </button>
                )}
              </div>
            </Field>
          </div>
          <div className="sm:col-span-2">
            <button type="submit" disabled={busy} className={buttonClasses("primary", "md")}>
              {busy ? <Spinner /> : "ذخیره تنظیمات"}
            </button>
          </div>
        </form>
      </Card>

      <Card title="همگام‌سازی رزروهای قبلی">
        <p className="mb-4 max-w-3xl text-sm leading-7 text-fg-muted">
          رزروهای قطعی بازه‌ای که هنوز سند فروش ندارند (مثلاً قبل از روشن شدن حسابداری) ثبت می‌شوند؛ هر رزرو فقط یک‌بار ثبت می‌شود، پس اجرای دوباره بی‌خطر است.
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <Field label="از">
            <SingleDatePicker value={from} onChange={setFrom} label="از تاریخ" />
          </Field>
          <Field label="تا">
            <SingleDatePicker value={to} onChange={setTo} label="تا تاریخ" />
          </Field>
          <button type="button" onClick={sync} disabled={busy} className={buttonClasses("dark", "md")}>
            همگام‌سازی
          </button>
        </div>
      </Card>

      <Card title="بستن سال مالی">
        <p className="mb-4 max-w-3xl text-sm leading-7 text-fg-muted">
          پایان سال: درآمدها و هزینه‌های آن سال با یک سند به «سود انباشته» منتقل و سال قفل می‌شود. گزارش سود و زیان همان سال بعد از بستن هم کامل دیده می‌شود. فقط سال‌های تمام‌شده بسته می‌شوند.
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <Field label="سال">
            <input className="field w-28" dir="ltr" value={fa(closeYear)} onChange={(e) => setCloseYear(Number(toLatinDigits(e.target.value).replace(/\D/g, "")) || closeYear)} />
          </Field>
          <button type="button" onClick={closeFiscalYear} disabled={busy} className={buttonClasses("signal", "md")}>
            بستن سال
          </button>
        </div>
      </Card>
    </div>
  );
}
