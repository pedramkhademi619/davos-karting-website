"use client";

import { useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card } from "@/components/admin/admin-ui";
import { Field } from "@/components/admin/accounting/accounting-fields";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { ACCOUNT_TYPE_LABEL, type Account, type AccountType } from "@/lib/accounting";
import { fa } from "@/lib/format";

const TYPES: AccountType[] = ["asset", "liability", "equity", "revenue", "expense"];

type Draft = { id: string | null; code: string; name: string; type: AccountType; parent: string; group: boolean; active: boolean };
const blank = (): Draft => ({ id: null, code: "", name: "", type: "expense", parent: "", group: false, active: true });

/** The chart of accounts as a tree. Accounts with a system role can be renamed or renumbered but not deleted. */
export function ChartView({ accounts, onChanged }: { accounts: Account[]; onChanged: () => void }) {
  const { call } = useAdmin();
  const [draft, setDraft] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const children = (parent: string | null) => accounts.filter((a) => a.parent_id === parent).sort((a, b) => a.code.localeCompare(b.code));

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setBusy(true);
    setError(null);
    try {
      const body = { code: draft.code, name: draft.name, type: draft.type, parent_id: draft.parent || null, is_group: draft.group, active: draft.active };
      if (draft.id) await call(`/accounting/accounts/${draft.id}`, { method: "PUT", body });
      else await call("/accounting/accounts", { method: "POST", body });
      setDraft(null);
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function remove(account: Account) {
    if (!window.confirm(`حساب «${account.name}» حذف شود؟`)) return;
    try {
      await call(`/accounting/accounts/${account.id}`, { method: "DELETE" });
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  const renderLevel = (parent: string | null, depth: number) =>
    children(parent).map((account) => (
      <li key={account.id}>
        <div className={`flex flex-wrap items-center gap-3 rounded-xl px-3 py-2 ${account.is_group ? "bg-surface-2 font-black" : "hover:bg-surface-2"} ${account.active ? "" : "opacity-50"}`} style={{ marginRight: depth * 20 }}>
          <span className="w-14 text-sm text-fg-muted">{fa(account.code)}</span>
          <span className="flex-1">{account.name}</span>
          {account.is_system && <span className="rounded-full bg-wait-soft px-2 py-0.5 text-xs font-bold text-ink-soft">سیستمی</span>}
          {!account.active && <span className="text-xs text-fg-subtle">غیرفعال</span>}
          <button type="button" className="text-sm font-bold underline underline-offset-4" onClick={() => setDraft({ id: account.id, code: account.code, name: account.name, type: account.type, parent: account.parent_id ?? "", group: account.is_group, active: account.active })}>
            ویرایش
          </button>
          {account.is_group && (
            <button type="button" className="text-sm font-bold underline underline-offset-4" onClick={() => setDraft({ ...blank(), type: account.type, parent: account.id })}>
              + زیرحساب
            </button>
          )}
          {!account.is_system && !account.is_group && (
            <button type="button" className="text-sm font-bold text-signal underline underline-offset-4" onClick={() => remove(account)}>
              حذف
            </button>
          )}
        </div>
        {account.is_group && <ul>{renderLevel(account.id, depth + 1)}</ul>}
      </li>
    ));

  return (
    <div className="space-y-6">
      {error && <Alert tone="error">{error}</Alert>}
      {draft && (
        <Card title={draft.id ? "ویرایش حساب" : "حساب جدید"}>
          <form onSubmit={save} className="grid max-w-3xl gap-4 sm:grid-cols-2">
            <Field label="کد حساب">
              <input className="field" dir="ltr" value={draft.code} onChange={(e) => setDraft({ ...draft, code: e.target.value })} maxLength={20} required />
            </Field>
            <Field label="نام حساب">
              <input className="field" value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} maxLength={120} required />
            </Field>
            {!draft.id && (
              <>
                <Field label="نوع">
                  <select className="field" value={draft.type} onChange={(e) => setDraft({ ...draft, type: e.target.value as AccountType, parent: "" })}>
                    {TYPES.map((t) => (
                      <option key={t} value={t}>
                        {ACCOUNT_TYPE_LABEL[t]}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="زیر سرفصل">
                  <select className="field" value={draft.parent} onChange={(e) => setDraft({ ...draft, parent: e.target.value })}>
                    <option value="">بدون والد (سرفصل اصلی)</option>
                    {accounts.filter((a) => a.is_group && a.type === draft.type).map((a) => (
                      <option key={a.id} value={a.id}>
                        {fa(a.code)} · {a.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <label className="flex items-center gap-3 text-sm font-bold sm:col-span-2">
                  <input type="checkbox" className="h-5 w-5 accent-[#0c0d10]" checked={draft.group} onChange={(e) => setDraft({ ...draft, group: e.target.checked })} />
                  سرفصل گروه (فقط جمع زیرحساب‌ها؛ سند روی آن زده نمی‌شود)
                </label>
              </>
            )}
            {draft.id && (
              <label className="flex items-center gap-3 text-sm font-bold sm:col-span-2">
                <input type="checkbox" className="h-5 w-5 accent-[#0c0d10]" checked={draft.active} onChange={(e) => setDraft({ ...draft, active: e.target.checked })} />
                حساب فعال است
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
      <div className="flex justify-end">
        <button type="button" onClick={() => setDraft(blank())} className={buttonClasses("primary", "sm")}>
          حساب جدید
        </button>
      </div>
      <ul className="space-y-1">{renderLevel(null, 0)}</ul>
    </div>
  );
}
