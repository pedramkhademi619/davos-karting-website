"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Kpi, Pager, TabHeader, Table, cell } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { SMS_STATUS, dateTime, fa, mobile, toLatinDigits, toman } from "@/lib/format";
import { currentBusinessDay, isoToJalali, parseJalali } from "@/lib/jalali";
import type { Page, SmsAccount, SmsLog, SmsSent } from "@/lib/types";

const LIMIT = 50;
const MAX_TEXT = 600;

/** Kavenegar: credit, sending one text to typed numbers / SMS-news subscribers / one day's customers, and the delivery log. */
export function SmsTab() {
  const { call } = useAdmin();
  const [account, setAccount] = useState<SmsAccount | null>(null);
  const [log, setLog] = useState<Page<SmsLog> | null>(null);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    call<SmsAccount>("/sms/account")
      .then((result) => !cancelled && setAccount(result))
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, version]);

  useEffect(() => {
    let cancelled = false;
    call<Page<SmsLog>>("/sms/messages", { query: { offset, limit: LIMIT } })
      .then((result) => !cancelled && setLog(result))
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, offset, version]);

  return (
    <div>
      <TabHeader title="پنل پیامک" lead="ارسال از خط اختصاصی کاوه‌نگار. پیامک خبری فقط برای مشتریانی می‌رود که در حساب خود اجازه داده‌اند." />
      {error && (
        <Alert tone="error" className="mb-6">
          {error}
        </Alert>
      )}
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="space-y-6 xl:col-span-5">
          <div className="grid grid-cols-2 gap-4">
            <Kpi
              tone="dark"
              label="اعتبار کاوه‌نگار"
              value={<span className="text-2xl">{account?.remaining_credit_toman != null ? toman(account.remaining_credit_toman) : "—"}</span>}
            />
            <Kpi
              label="اتصال"
              value={<span className="text-xl">{account ? (account.connected ? "برقرار" : "قطع") : "…"}</span>}
              note={account ? (account.provider === "kavenegar" ? "کاوه‌نگار" : "حالت آزمایشی (ارسال واقعی نمی‌شود)") : undefined}
            />
          </div>
          <SendForm onSent={() => setVersion((v) => v + 1)} />
        </div>
        <div className="xl:col-span-7">
          <Card title="پیامک‌های ارسال‌شده">
            {!log ? (
              <Spinner className="h-7 w-7" />
            ) : (
              <>
                <Table head={["زمان", "گیرنده", "متن", "وضعیت", "ارسال‌کننده"]} empty={log.items.length === 0}>
                  {log.items.map((m) => (
                    <tr key={m.id}>
                      <td className={cell}>{dateTime(m.created_at)}</td>
                      <td className={cell} dir="ltr">
                        {mobile(m.recipient)}
                      </td>
                      <td className={`${cell} max-w-[18rem] truncate`} title={m.body}>
                        {m.body}
                      </td>
                      <td className={cell}>
                        {SMS_STATUS[m.status] ?? m.status}
                        {m.error && <span className="block text-xs text-signal">{m.error}</span>}
                      </td>
                      <td className={cell}>{m.kind === "bulk" ? m.sent_by || "پنل" : "خودکار"}</td>
                    </tr>
                  ))}
                </Table>
                <Pager offset={offset} limit={LIMIT} total={log.total} onChange={setOffset} />
              </>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

function SendForm({ onSent }: { onSent: () => void }) {
  const { call } = useAdmin();
  const [audience, setAudience] = useState<"numbers" | "subscribers" | "day">("numbers");
  const [numbers, setNumbers] = useState("");
  const [day, setDay] = useState(() => isoToJalali(currentBusinessDay()));
  const [text, setText] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  // Persian texts are sent as Unicode: 70 characters in one SMS, 67 per part when longer.
  const parts = text.length <= 70 ? 1 : Math.ceil(text.length / 67);
  const numberList = toLatinDigits(numbers)
    .split(/[\s,،;]+/)
    .map((n) => n.trim())
    .filter(Boolean);

  async function send(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    const isoDay = audience === "day" ? parseJalali(day) : null;
    if (audience === "day" && !isoDay) {
      setMessage({ tone: "error", text: "تاریخ را به شکل ۱۴۰۵/۰۷/۰۴ وارد کنید." });
      return;
    }
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const result = await call<SmsSent>("/sms/send", {
        method: "POST",
        body: { audience, numbers: audience === "numbers" ? numberList : [], day: isoDay, text: text.trim() },
      });
      const invalid = result.invalid_numbers.length ? ` شماره‌های نامعتبر: ${result.invalid_numbers.join("، ")}` : "";
      setMessage({ tone: "success", text: `${fa(result.accepted)} پیامک پذیرفته شد، ${fa(result.failed)} ناموفق.${invalid}` });
      setText("");
      onSent();
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  }

  const audienceLabel = { numbers: `${fa(numberList.length)} شماره`, subscribers: "همه مشترکان خبرنامه", day: `مشتریان روز ${fa(day)}` }[audience];

  return (
    <form onSubmit={send} className="panel space-y-4 p-6">
      <h2 className="text-lg font-black">ارسال پیامک</h2>
      <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="گیرندگان">
        {(
          [
            ["numbers", "شماره‌های دلخواه"],
            ["subscribers", "مشترکان خبرنامه"],
            ["day", "مشتریان یک روز"],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={audience === value}
            onClick={() => {
              setAudience(value);
              setConfirming(false);
            }}
            className={`rounded-full border-2 px-4 py-2 text-sm font-bold ${audience === value ? "border-ink bg-ink text-accent" : "border-line-strong text-fg-muted"}`}
          >
            {label}
          </button>
        ))}
      </div>
      {audience === "numbers" && (
        <label className="block">
          <span className="label">شماره‌ها (هر خط یا با کاما جدا)</span>
          <textarea className="field" dir="ltr" rows={4} value={numbers} onChange={(e) => setNumbers(e.target.value)} />
        </label>
      )}
      {audience === "day" && (
        <label className="block">
          <span className="label">روز (شمسی)</span>
          <input className="field" dir="ltr" value={fa(day)} onChange={(e) => setDay(e.target.value)} />
        </label>
      )}
      <label className="block">
        <span className="label">متن پیامک</span>
        <textarea className="field" rows={5} maxLength={MAX_TEXT} value={text} onChange={(e) => setText(e.target.value)} />
        <span className="mt-1 block text-xs text-fg-subtle">
          {fa(text.length)} از {fa(MAX_TEXT)} نویسه · حدود {fa(parts)} پیامک برای هر گیرنده
        </span>
      </label>
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      {confirming && (
        <Alert tone="warning">
          ارسال به {audienceLabel} انجام شود؟ این کار از اعتبار پنل کم می‌کند و قابل برگشت نیست. برای تایید دوباره «ارسال» را بزنید.
        </Alert>
      )}
      <div className="flex gap-3">
        <button type="submit" disabled={busy || !text.trim() || (audience === "numbers" && numberList.length === 0)} className={buttonClasses("primary", "md")}>
          {busy ? <Spinner /> : confirming ? "بله، ارسال" : "ارسال"}
        </button>
        {confirming && (
          <button type="button" className={buttonClasses("ghost", "md")} onClick={() => setConfirming(false)}>
            انصراف
          </button>
        )}
      </div>
    </form>
  );
}
