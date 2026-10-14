"use client";

import { useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { SingleDatePicker } from "@/components/admin/date-picker-field";
import { AccountSelect, Field, MoneyInput, VendorSelect } from "@/components/admin/accounting/accounting-fields";
import { Card } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import type { Account, Entry, Vendor } from "@/lib/accounting";
import { fa } from "@/lib/format";
import { currentBusinessDay } from "@/lib/jalali";

type Kind = "expense" | "income" | "transfer" | "vendor" | "refund";

const KINDS: { id: Kind; label: string; hint: string }[] = [
  { id: "expense", label: "ثبت هزینه", hint: "سوخت، تعمیر، اجاره، حقوق...؛ نقدی از صندوق یا بانک، یا نسیه به تامین‌کننده." },
  { id: "income", label: "درآمد متفرقه", hint: "پولی که بابت بلیت نیست: اسپانسر، بوفه، اجاره پیست." },
  { id: "transfer", label: "انتقال وجه", hint: "از صندوق به بانک، تسویه درگاه به بانک و مانند آن." },
  { id: "vendor", label: "پرداخت به تامین‌کننده", hint: "تسویه (بخشی از) بدهی نسیه به یک تامین‌کننده." },
  { id: "refund", label: "پرداخت استرداد مشتری", hint: "پولی که برای بلیت لغوشده به مشتری برگردانده می‌شود." },
];

/** The everyday entries in business words; the system turns each into a balanced journal entry. */
export function QuickEntry({ accounts, vendors, onDone }: { accounts: Account[]; vendors: Vendor[]; onDone: () => void }) {
  const { call } = useAdmin();
  const [kind, setKind] = useState<Kind>("expense");
  const [day, setDay] = useState(currentBusinessDay());
  const [amount, setAmount] = useState(0);
  const [vat, setVat] = useState(0);
  const [main, setMain] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [vendor, setVendor] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  const cashLike = ["cash", "bank", "pos", "gateway"];

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      let entry: Entry;
      const base = { date: day, amount_toman: amount, description };
      if (kind === "expense") {
        entry = await call<Entry>("/accounting/expenses", {
          method: "POST",
          body: { ...base, expense_account_id: main, vat_toman: vat, paid_from_account_id: from || null, vendor_id: vendor || null },
        });
      } else if (kind === "income") {
        entry = await call<Entry>("/accounting/income", {
          method: "POST",
          body: { ...base, revenue_account_id: main, vat_toman: vat, deposit_account_id: to },
        });
      } else if (kind === "transfer") {
        entry = await call<Entry>("/accounting/transfers", { method: "POST", body: { ...base, from_account_id: from, to_account_id: to } });
      } else {
        entry = await call<Entry>("/accounting/payments", {
          method: "POST",
          body: { ...base, from_account_id: from, vendor_id: kind === "vendor" ? vendor : null },
        });
      }
      setMessage({ tone: "success", text: `ثبت شد؛ سند شماره ${fa(entry.number)} (سال ${fa(entry.fiscal_year)}).` });
      setAmount(0);
      setVat(0);
      setDescription("");
      onDone();
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <div role="tablist" aria-label="نوع ثبت" className="mb-5 flex flex-wrap gap-2">
        {KINDS.map((k) => (
          <button
            key={k.id}
            type="button"
            role="tab"
            aria-selected={kind === k.id}
            onClick={() => {
              setKind(k.id);
              setMessage(null);
            }}
            className={`rounded-full px-4 py-2 text-sm font-bold ring-1 transition-colors ${kind === k.id ? "bg-ink text-white ring-ink" : "bg-surface text-fg-muted ring-line-strong hover:text-fg"}`}
          >
            {k.label}
          </button>
        ))}
      </div>
      <p className="mb-5 text-sm leading-7 text-fg-muted">{KINDS.find((k) => k.id === kind)?.hint}</p>

      <form onSubmit={submit} className="grid max-w-3xl gap-4 sm:grid-cols-2">
        <Field label="تاریخ">
          <SingleDatePicker value={day} onChange={setDay} label="تاریخ" />
        </Field>
        <MoneyInput label="مبلغ کل (تومان)" value={amount} onChange={setAmount} />

        {kind === "expense" && (
          <>
            <AccountSelect label="حساب هزینه" accounts={accounts} value={main} onChange={setMain} types={["expense", "asset"]} />
            <AccountSelect label="پرداخت از" accounts={accounts} value={from} onChange={setFrom} types={["asset"]} roles={cashLike} allowEmpty="نسیه (بدهی به تامین‌کننده)" />
            <VendorSelect label="تامین‌کننده" vendors={vendors} value={vendor} onChange={setVendor} allowEmpty="بدون تامین‌کننده" />
            <MoneyInput label="مالیات ارزش افزوده داخل مبلغ (تومان)" value={vat} onChange={setVat} hint="اگر فاکتور مالیات دارد؛ بخشی از مبلغ کل است." />
          </>
        )}
        {kind === "income" && (
          <>
            <AccountSelect label="حساب درآمد" accounts={accounts} value={main} onChange={setMain} types={["revenue"]} />
            <AccountSelect label="واریز به" accounts={accounts} value={to} onChange={setTo} types={["asset"]} roles={cashLike} />
            <MoneyInput label="مالیات ارزش افزوده داخل مبلغ (تومان)" value={vat} onChange={setVat} />
          </>
        )}
        {kind === "transfer" && (
          <>
            <AccountSelect label="از حساب" accounts={accounts} value={from} onChange={setFrom} types={["asset"]} roles={cashLike} />
            <AccountSelect label="به حساب" accounts={accounts} value={to} onChange={setTo} types={["asset"]} roles={cashLike} />
          </>
        )}
        {kind === "vendor" && (
          <>
            <VendorSelect label="تامین‌کننده" vendors={vendors} value={vendor} onChange={setVendor} />
            <AccountSelect label="پرداخت از" accounts={accounts} value={from} onChange={setFrom} types={["asset"]} roles={cashLike} />
          </>
        )}
        {kind === "refund" && <AccountSelect label="پرداخت از" accounts={accounts} value={from} onChange={setFrom} types={["asset"]} roles={cashLike} />}

        <div className="sm:col-span-2">
          <Field label="شرح (اختیاری)">
            <input className="field" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={300} />
          </Field>
        </div>
        {message && (
          <div className="sm:col-span-2">
            <Alert tone={message.tone}>{message.text}</Alert>
          </div>
        )}
        <div className="sm:col-span-2">
          <button type="submit" disabled={busy || amount <= 0} className={buttonClasses("primary", "md")}>
            {busy ? <Spinner /> : "ثبت سند"}
          </button>
        </div>
      </form>
    </Card>
  );
}
