"use client";

import { useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Table, cell } from "@/components/admin/admin-ui";
import { Field } from "@/components/admin/accounting/accounting-fields";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { toman, tomanOrDash, type Vendor } from "@/lib/accounting";
import { fa } from "@/lib/format";

type Draft = { id: string | null; name: string; phone: string; note: string; active: boolean };

/** Suppliers and what is owed to each, aged by the date of each unpaid bill. */
export function VendorsView({ vendors, onChanged }: { vendors: Vendor[]; onChanged: () => void }) {
  const { call } = useAdmin();
  const [draft, setDraft] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setBusy(true);
    setError(null);
    try {
      const body = { name: draft.name, phone: draft.phone, note: draft.note, active: draft.active };
      if (draft.id) await call(`/accounting/vendors/${draft.id}`, { method: "PUT", body });
      else await call("/accounting/vendors", { method: "POST", body });
      setDraft(null);
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const totalOwed = vendors.reduce((sum, v) => sum + v.owed_irr, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-bold">مجموع بدهی به تامین‌کنندگان: {toman(totalOwed)} تومان</p>
        <button type="button" className={buttonClasses("primary", "sm")} onClick={() => setDraft({ id: null, name: "", phone: "", note: "", active: true })}>
          تامین‌کننده جدید
        </button>
      </div>
      {error && <Alert tone="error">{error}</Alert>}
      {draft && (
        <Card title={draft.id ? "ویرایش تامین‌کننده" : "تامین‌کننده جدید"}>
          <form onSubmit={save} className="grid max-w-3xl gap-4 sm:grid-cols-2">
            <Field label="نام">
              <input className="field" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} maxLength={120} required />
            </Field>
            <Field label="تلفن">
              <input className="field" dir="ltr" value={draft.phone} onChange={(e) => setDraft({ ...draft, phone: e.target.value })} maxLength={20} />
            </Field>
            <div className="sm:col-span-2">
              <Field label="توضیح">
                <input className="field" value={draft.note} onChange={(e) => setDraft({ ...draft, note: e.target.value })} maxLength={300} />
              </Field>
            </div>
            {draft.id && (
              <label className="flex items-center gap-3 text-sm font-bold sm:col-span-2">
                <input type="checkbox" className="h-5 w-5 accent-[#0c0d10]" checked={draft.active} onChange={(e) => setDraft({ ...draft, active: e.target.checked })} />
                فعال است
              </label>
            )}
            <div className="flex gap-3 sm:col-span-2">
              <button type="submit" disabled={busy} className={buttonClasses("primary", "md")}>
                {busy ? <Spinner /> : "ذخیره"}
              </button>
              <button type="button" onClick={() => setDraft(null)} className={buttonClasses("ghost", "md")}>
                انصراف
              </button>
            </div>
          </form>
        </Card>
      )}
      <Table head={["تامین‌کننده", "تلفن", "بدهی کل", "تا ۳۰ روز", "۳۱ تا ۶۰", "۶۱ تا ۹۰", "بیش از ۹۰", "پیش‌پرداخت", ""]} empty={vendors.length === 0}>
        {vendors.map((v) => (
          <tr key={v.id} className={v.active ? "" : "opacity-50"}>
            <td className={`${cell} font-bold`}>{v.name}</td>
            <td className={cell} dir="ltr">{v.phone ? fa(v.phone) : "—"}</td>
            <td className={`${cell} font-black`}>{tomanOrDash(v.owed_irr)}</td>
            <td className={cell}>{tomanOrDash(v.age_0_30_irr)}</td>
            <td className={cell}>{tomanOrDash(v.age_31_60_irr)}</td>
            <td className={cell}>{tomanOrDash(v.age_61_90_irr)}</td>
            <td className={`${cell} ${v.age_over_90_irr ? "font-black text-signal" : ""}`}>{tomanOrDash(v.age_over_90_irr)}</td>
            <td className={cell}>{tomanOrDash(v.advance_irr)}</td>
            <td className={cell}>
              <button type="button" className="font-bold underline underline-offset-4" onClick={() => setDraft({ id: v.id, name: v.name, phone: v.phone, note: v.note, active: v.active })}>
                ویرایش
              </button>
            </td>
          </tr>
        ))}
      </Table>
    </div>
  );
}
