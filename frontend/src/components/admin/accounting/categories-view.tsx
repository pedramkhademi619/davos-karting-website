"use client";

import { useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card } from "@/components/admin/admin-ui";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { categories, categoryParent, nextCategoryCode, type Account } from "@/lib/accounting";
import { fa } from "@/lib/format";

type Kind = "expense" | "revenue";

/** The income and expense categories the owner picks from when recording money: add, rename, hide or bring back. */
export function CategoriesView({ accounts, onChanged }: { accounts: Account[]; onChanged: () => void }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <CategoryList kind="expense" title="دسته‌های هزینه" accounts={accounts} onChanged={onChanged} />
      <CategoryList kind="revenue" title="دسته‌های درآمد" accounts={accounts} onChanged={onChanged} />
      <p className="text-sm leading-7 text-fg-muted lg:col-span-2">
        فروش بلیت، استرداد، کارمزد بانک و کسری صندوق خودکار ثبت می‌شوند و اینجا نمی‌آیند. دسته‌ای که پنهان کنید در فرم ثبت دیده نمی‌شود، ولی
        گزارش‌های قبلی‌اش سر جایش می‌ماند.
      </p>
    </div>
  );
}

function CategoryList({ kind, title, accounts, onChanged }: { kind: Kind; title: string; accounts: Account[]; onChanged: () => void }) {
  const { call } = useAdmin();
  const [name, setName] = useState("");
  const [editing, setEditing] = useState<{ id: string; name: string } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const all = categories(accounts, kind, true);
  const shown = all.filter((a) => a.active);
  const hidden = all.filter((a) => !a.active);
  const parent = categoryParent(accounts, kind);

  async function run(key: string, action: () => Promise<unknown>) {
    setBusy(key);
    setError(null);
    try {
      await action();
      onChanged();
      return true;
    } catch (err) {
      setError(errorMessage(err));
      return false;
    } finally {
      setBusy(null);
    }
  }

  const save = (account: Account, changes: Partial<Pick<Account, "name" | "active">>) =>
    call(`/accounting/accounts/${account.id}`, {
      method: "PUT",
      body: { code: account.code, name: account.name, type: account.type, parent_id: account.parent_id, is_group: false, active: account.active, ...changes },
    });

  async function add(event: FormEvent) {
    event.preventDefault();
    const clean = name.trim();
    if (!clean) return;
    const ok = await run("new", () =>
      call("/accounting/accounts", { method: "POST", body: { code: nextCategoryCode(accounts, kind), name: clean, type: kind, parent_id: parent?.id ?? null, is_group: false } }),
    );
    if (ok) setName("");
  }

  return (
    <Card title={title}>
      <ul className="divide-y divide-line">
        {shown.map((account) => (
          <li key={account.id} className="flex items-center gap-3 py-2.5">
            {editing?.id === account.id ? (
              <form
                className="flex flex-1 gap-2"
                onSubmit={async (event) => {
                  event.preventDefault();
                  if (await run(account.id, () => save(account, { name: editing.name.trim() }))) setEditing(null);
                }}
              >
                <input className="field !h-10 flex-1" value={editing.name} onChange={(e) => setEditing({ id: account.id, name: e.target.value })} maxLength={120} autoFocus />
                <button type="submit" disabled={!editing.name.trim() || busy === account.id} className="rounded-full bg-ink px-4 text-sm font-bold text-white">
                  {busy === account.id ? <Spinner /> : "ذخیره"}
                </button>
                <button type="button" onClick={() => setEditing(null)} className="rounded-full px-3 text-sm font-bold ring-1 ring-line-strong">
                  لغو
                </button>
              </form>
            ) : (
              <>
                <span className="flex-1 font-bold">{account.name}</span>
                <button type="button" onClick={() => setEditing({ id: account.id, name: account.name })} className="rounded-full px-3 py-1.5 text-xs font-bold text-fg-muted ring-1 ring-line-strong hover:text-fg">
                  تغییر نام
                </button>
                <button
                  type="button"
                  disabled={busy === account.id}
                  onClick={() => run(account.id, () => save(account, { active: false }))}
                  className="min-w-16 rounded-full px-3 py-1.5 text-xs font-bold text-fg-muted ring-1 ring-line-strong hover:text-fg"
                >
                  {busy === account.id ? <Spinner /> : "پنهان"}
                </button>
              </>
            )}
          </li>
        ))}
      </ul>
      {hidden.length > 0 && (
        <details className="mt-3 rounded-2xl bg-surface-2 px-4 py-2">
          <summary className="cursor-pointer py-1 text-sm font-bold text-fg-muted">پنهان‌شده‌ها ({fa(hidden.length)})</summary>
          <ul className="divide-y divide-line">
            {hidden.map((account) => (
              <li key={account.id} className="flex items-center gap-3 py-2">
                <span className="flex-1 text-sm text-fg-muted">{account.name}</span>
                <button
                  type="button"
                  disabled={busy === account.id}
                  onClick={() => run(account.id, () => save(account, { active: true }))}
                  className="min-w-16 rounded-full px-3 py-1.5 text-xs font-bold text-fg-muted ring-1 ring-line-strong hover:text-fg"
                >
                  {busy === account.id ? <Spinner /> : "نمایش"}
                </button>
              </li>
            ))}
          </ul>
        </details>
      )}
      <form onSubmit={add} className="mt-4 flex gap-2">
        <input className="field flex-1" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} placeholder={kind === "expense" ? "دسته‌ی تازه، مثلاً «نوشیدنی بوفه»" : "مثلاً «اسپانسر»"} />
        <button type="submit" disabled={!name.trim() || busy === "new"} className="rounded-full bg-ink px-5 font-bold text-white disabled:opacity-40">
          {busy === "new" ? <Spinner /> : "افزودن"}
        </button>
      </form>
      {error && <Alert tone="error" className="mt-3">{error}</Alert>}
    </Card>
  );
}
