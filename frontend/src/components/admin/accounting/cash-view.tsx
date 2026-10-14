"use client";

import { useCallback, useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Table, cell } from "@/components/admin/admin-ui";
import { SingleDatePicker } from "@/components/admin/date-picker-field";
import { Field, MoneyInput } from "@/components/admin/accounting/accounting-fields";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { toman, type CashClosing } from "@/lib/accounting";
import { fa } from "@/lib/format";
import { currentBusinessDay, isoToJalali } from "@/lib/jalali";

type CashState = { date: string; expected_irr: number; closings: CashClosing[] };

/** End-of-day count of the till. The difference from what the books expect is booked as overage or shortage. */
export function CashView({ onChanged }: { onChanged: () => void }) {
  const { call } = useAdmin();
  const [day, setDay] = useState(currentBusinessDay());
  const [state, setState] = useState<CashState | null>(null);
  const [counted, setCounted] = useState(0);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setState(await call<CashState>("/accounting/cash", { query: { date: day } }));
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [call, day]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reloads when the day changes
    void load();
  }, [load]);

  async function close() {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await call<CashClosing>("/accounting/cash", { method: "POST", body: { date: day, counted_toman: counted, note } });
      setMessage(result.difference_irr === 0 ? "صندوق بسته شد؛ مبلغ دقیقاً با دفتر برابر بود." : `صندوق بسته شد؛ ${result.difference_irr > 0 ? "اضافه" : "کسری"} ${toman(Math.abs(result.difference_irr))} تومان ثبت شد.`);
      setCounted(0);
      setNote("");
      await load();
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const expected = state?.expected_irr ?? 0;
  const difference = counted * 10 - expected;

  return (
    <div className="space-y-6">
      <Card title="بستن صندوق روز">
        <div className="grid max-w-3xl gap-4 sm:grid-cols-2">
          <Field label="روز">
            <SingleDatePicker value={day} onChange={setDay} label="روز صندوق" />
          </Field>
          <div>
            <p className="label">موجودی صندوق طبق دفاتر (تومان)</p>
            <p className="mt-2 text-2xl font-black">{state ? toman(expected) : <Spinner />}</p>
          </div>
          <MoneyInput label="مبلغ شمارش‌شده (تومان)" value={counted} onChange={setCounted} />
          <div>
            <p className="label">اختلاف</p>
            <p className={`mt-2 text-xl font-black ${difference === 0 ? "" : difference > 0 ? "text-go" : "text-signal"}`}>
              {counted === 0 && difference === -expected && expected === 0 ? "—" : `${toman(difference)} ${difference > 0 ? "(اضافه)" : difference < 0 ? "(کسری)" : ""}`}
            </p>
          </div>
          <div className="sm:col-span-2">
            <Field label="یادداشت">
              <input className="field" value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} />
            </Field>
          </div>
          <div className="sm:col-span-2">
            <button type="button" onClick={close} disabled={busy} className={buttonClasses("primary", "md")}>
              {busy ? <Spinner /> : "بستن صندوق"}
            </button>
          </div>
        </div>
        {message && <Alert tone="success" className="mt-4">{message}</Alert>}
        {error && <Alert tone="error" className="mt-4">{error}</Alert>}
      </Card>
      <Table head={["روز", "طبق دفاتر", "شمارش‌شده", "اختلاف", "ثبت‌کننده", "یادداشت"]} empty={!!state && state.closings.length === 0}>
        {(state?.closings ?? []).map((c) => (
          <tr key={c.id}>
            <td className={cell}>{fa(isoToJalali(c.date))}</td>
            <td className={cell}>{toman(c.expected_irr)}</td>
            <td className={cell}>{toman(c.counted_irr)}</td>
            <td className={`${cell} font-black ${c.difference_irr < 0 ? "text-signal" : c.difference_irr > 0 ? "text-go" : ""}`}>{toman(c.difference_irr)}</td>
            <td className={cell}>{c.closed_by}</td>
            <td className={cell}>{c.note || "—"}</td>
          </tr>
        ))}
      </Table>
    </div>
  );
}
