"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Table, cell } from "@/components/admin/admin-ui";
import { AccountSelect, Field, MoneyInput } from "@/components/admin/accounting/accounting-fields";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { toman, type Account, type BudgetRow } from "@/lib/accounting";
import { fa, toLatinDigits } from "@/lib/format";
import { JALALI_MONTHS, currentBusinessDay, isoToJalaliParts } from "@/lib/jalali";

/** A budget per revenue or expense account and how the real numbers compare. */
export function BudgetView({ accounts }: { accounts: Account[] }) {
  const { call } = useAdmin();
  const now = isoToJalaliParts(currentBusinessDay());
  const [year, setYear] = useState(now.jy);
  const [from, setFrom] = useState(1);
  const [to, setTo] = useState(now.jm);
  const [rows, setRows] = useState<BudgetRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  const load = useCallback(async () => {
    try {
      setRows(await call<BudgetRow[]>("/accounting/budget", { query: { year, month_from: from, month_to: to } }));
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [call, year, from, to]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reloads when the period changes
    void load();
  }, [load, version]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-3">
        <Field label="سال">
          <input className="field w-24" dir="ltr" value={fa(year)} onChange={(e) => setYear(Number(toLatinDigits(e.target.value).replace(/\D/g, "")) || now.jy)} />
        </Field>
        <Field label="از ماه">
          <select className="field w-36" value={from} onChange={(e) => setFrom(Number(e.target.value))}>
            {JALALI_MONTHS.map((m, i) => (
              <option key={m} value={i + 1} disabled={i + 1 > to}>
                {m}
              </option>
            ))}
          </select>
        </Field>
        <Field label="تا ماه">
          <select className="field w-36" value={to} onChange={(e) => setTo(Number(e.target.value))}>
            {JALALI_MONTHS.map((m, i) => (
              <option key={m} value={i + 1} disabled={i + 1 < from}>
                {m}
              </option>
            ))}
          </select>
        </Field>
      </div>
      {error && <Alert tone="error">{error}</Alert>}
      <SetBudget accounts={accounts} year={year} onSaved={() => setVersion((v) => v + 1)} />
      {!rows ? (
        <Spinner className="h-8 w-8" />
      ) : (
        <Table head={["حساب", "نوع", "بودجه", "واقعی", "اختلاف", "درصد تحقق"]} empty={rows.length === 0}>
          {rows.map((r) => {
            const over = r.type === "expense" ? r.variance_irr > 0 : r.variance_irr < 0;
            return (
              <tr key={r.account_id}>
                <td className={`${cell} font-bold`}>{fa(r.code)} · {r.name}</td>
                <td className={cell}>{r.type === "revenue" ? "درآمد" : "هزینه"}</td>
                <td className={cell}>{toman(r.budget_irr)}</td>
                <td className={cell}>{toman(r.actual_irr)}</td>
                <td className={`${cell} font-black ${r.budget_irr && over ? "text-signal" : "text-go"}`}>{toman(r.variance_irr)}</td>
                <td className={cell}>{r.budget_irr ? `${fa(Math.round((r.actual_irr / r.budget_irr) * 100))}٪` : "—"}</td>
              </tr>
            );
          })}
        </Table>
      )}
    </div>
  );
}

function SetBudget({ accounts, year, onSaved }: { accounts: Account[]; year: number; onSaved: () => void }) {
  const { call } = useAdmin();
  const [account, setAccount] = useState("");
  const [month, setMonth] = useState(0);
  const [amount, setAmount] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await call("/accounting/budget", { method: "PUT", body: { account_id: account, year, month: month || null, amount_toman: amount } });
      setAmount(0);
      onSaved();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="تعیین بودجه">
      <form onSubmit={submit} className="grid max-w-4xl gap-4 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <AccountSelect label="حساب" accounts={accounts} value={account} onChange={setAccount} types={["revenue", "expense"]} />
        </div>
        <Field label="برای">
          <select className="field" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            <option value={0}>کل سال (به‌طور مساوی)</option>
            {JALALI_MONTHS.map((m, i) => (
              <option key={m} value={i + 1}>
                {m}
              </option>
            ))}
          </select>
        </Field>
        <MoneyInput label="مبلغ (تومان)" value={amount} onChange={setAmount} hint="صفر = حذف بودجه" />
        {error && (
          <div className="sm:col-span-4">
            <Alert tone="error">{error}</Alert>
          </div>
        )}
        <div className="sm:col-span-4">
          <button type="submit" disabled={busy || !account} className={buttonClasses("dark", "md")}>
            {busy ? <Spinner /> : "ذخیره بودجه"}
          </button>
        </div>
      </form>
    </Card>
  );
}
