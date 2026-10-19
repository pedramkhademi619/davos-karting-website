"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { SingleDatePicker } from "@/components/admin/date-picker-field";
import { Field, MoneyInput, Segmented } from "@/components/admin/accounting/accounting-fields";
import { MonthStepper } from "@/components/admin/accounting/month-stepper";
import { buttonClasses } from "@/components/button-link";
import { CloseIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { PageSkeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { monthBounds, monthOf, toman, walletAccount, WALLET_LABEL, type Account, type JalaliMonth, type Wallet } from "@/lib/accounting";
import { fa } from "@/lib/format";
import { currentBusinessDay, isoToJalali } from "@/lib/jalali";

type Staff = {
  id: string;
  name: string;
  title: string;
  mobile: string;
  monthly_salary_irr: number;
  note: string;
  active: boolean;
  salary_paid_irr: number;
  bonus_paid_irr: number;
  remaining_irr: number;
};
type Payment = { id: string; kind: string; amount_irr: number; month_key: string; date: string; note: string; created_by: string };

const KIND_LABEL: Record<string, string> = { salary: "حقوق", advance: "مساعده", bonus: "پاداش" };
const monthKey = ({ year, month }: JalaliMonth) => `${year}-${String(month).padStart(2, "0")}`;

/** The people who work at the track and what each was paid this month; every payment is booked as a payroll expense. */
export function StaffView({ accounts, onChanged }: { accounts: Account[]; onChanged: () => void }) {
  const { call } = useAdmin();
  const [month, setMonth] = useState<JalaliMonth>(() => monthOf(currentBusinessDay()));
  const [list, setList] = useState<{ key: string; items: Staff[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Staff | "new" | null>(null);
  const [paying, setPaying] = useState<Staff | null>(null);
  const [history, setHistory] = useState<{ staff: Staff; items: Payment[] } | null>(null);
  const key = monthKey(month);

  const load = useCallback(async () => {
    try {
      const items = await call<Staff[]>("/accounting/staff", { query: { month: key } });
      setList({ key, items });
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [call, key]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reloads when the month changes
    void load();
  }, [load]);

  const shown = list?.key === key ? list.items : null;
  const totals = useMemo(() => {
    const items = (shown ?? []).filter((s) => s.active);
    return {
      salary: items.reduce((n, s) => n + s.monthly_salary_irr, 0),
      paid: items.reduce((n, s) => n + s.salary_paid_irr + s.bonus_paid_irr, 0),
      left: items.reduce((n, s) => n + s.remaining_irr, 0),
    };
  }, [shown]);

  async function openHistory(staff: Staff) {
    setHistory({ staff, items: [] });
    try {
      setHistory({ staff, items: await call<Payment[]>(`/accounting/staff/${staff.id}/payments`) });
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <MonthStepper month={month} onChange={setMonth} />
        <button type="button" onClick={() => setEditing("new")} className={buttonClasses("dark", "md")}>
          + کارمند تازه
        </button>
      </div>
      {error && <Alert tone="error">{error}</Alert>}
      {!shown ? (
        !error && <PageSkeleton variant="rows" />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <Summary label="جمع حقوق ماهانه" value={totals.salary} />
            <Summary label="پرداخت‌شده در این ماه" value={totals.paid} />
            <Summary label="مانده‌ی حقوق" value={totals.left} warn={totals.left > 0} />
          </div>
          {shown.length === 0 ? (
            <p className="panel p-8 text-center text-fg-muted">هنوز کارمندی ثبت نشده است. با «کارمند تازه» شروع کنید.</p>
          ) : (
            <ul className="space-y-3">
              {shown.map((s) => (
                <li key={s.id} className={`panel p-4 md:p-5 ${s.active ? "" : "opacity-60"}`}>
                  <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
                    <div className="min-w-44 flex-1">
                      <p className="text-lg font-black">
                        {s.name} {!s.active && <span className="text-xs font-bold text-fg-subtle">(کنار رفته)</span>}
                      </p>
                      <p className="text-sm text-fg-muted">
                        {[s.title, s.mobile && fa(s.mobile)].filter(Boolean).join(" · ") || "—"}
                      </p>
                    </div>
                    <Figure label="حقوق ماهانه" value={toman(s.monthly_salary_irr)} />
                    <Figure label="پرداخت‌شده" value={toman(s.salary_paid_irr)} note={s.bonus_paid_irr ? `+ پاداش ${toman(s.bonus_paid_irr)}` : undefined} />
                    <Figure label="مانده" value={toman(s.remaining_irr)} tone={s.active && s.remaining_irr > 0 ? "warn" : "ok"} />
                    <div className="flex flex-wrap gap-2">
                      {s.active && (
                        <button type="button" onClick={() => setPaying(s)} className={buttonClasses("primary", "sm")}>
                          پرداخت
                        </button>
                      )}
                      <button type="button" onClick={() => void openHistory(s)} className="rounded-full px-4 py-2 text-sm font-bold ring-1 ring-line-strong">
                        سابقه
                      </button>
                      <button type="button" onClick={() => setEditing(s)} className="rounded-full px-4 py-2 text-sm font-bold ring-1 ring-line-strong">
                        ویرایش
                      </button>
                    </div>
                  </div>
                  {s.note && <p className="mt-2 text-xs text-fg-subtle">{s.note}</p>}
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {editing && (
        <StaffForm
          member={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            void load();
          }}
        />
      )}
      {paying && (
        <PaySheet
          staff={paying}
          accounts={accounts}
          month={month}
          onClose={() => setPaying(null)}
          onPaid={() => {
            setPaying(null);
            void load();
            onChanged();
          }}
        />
      )}
      {history && (
        <Sheet title={`سابقه‌ی پرداخت: ${history.staff.name}`} onClose={() => setHistory(null)}>
          {history.items.length === 0 ? (
            <p className="text-fg-muted">هنوز پرداختی ثبت نشده است.</p>
          ) : (
            <ul className="divide-y divide-line">
              {history.items.map((p) => (
                <li key={p.id} className="flex items-center justify-between gap-3 py-3">
                  <div>
                    <p className="font-bold">
                      {KIND_LABEL[p.kind] ?? p.kind} <span className="text-xs font-normal text-fg-subtle">برای ماه {fa(p.month_key)}</span>
                    </p>
                    <p className="text-xs text-fg-subtle">
                      {fa(isoToJalali(p.date))}
                      {p.note ? ` · ${p.note}` : ""}
                    </p>
                  </div>
                  <span className="font-black">{toman(p.amount_irr)}</span>
                </li>
              ))}
            </ul>
          )}
        </Sheet>
      )}
    </div>
  );
}

function Summary({ label, value, warn = false }: { label: string; value: number; warn?: boolean }) {
  return (
    <div className="rounded-3xl bg-surface p-4 outline outline-1 outline-line">
      <p className="text-sm font-bold text-fg-muted">{label}</p>
      <p className={`mt-2 text-2xl font-black ${warn ? "text-signal" : ""}`}>{toman(value)}</p>
      <p className="text-xs text-fg-subtle">تومان</p>
    </div>
  );
}

function Figure({ label, value, note, tone = "ok" }: { label: string; value: string; note?: string; tone?: "ok" | "warn" }) {
  return (
    <div className="min-w-28">
      <p className="text-xs text-fg-subtle">{label}</p>
      <p className={`font-black ${tone === "warn" ? "text-signal" : ""}`}>{value}</p>
      {note && <p className="text-xs text-fg-subtle">{note}</p>}
    </div>
  );
}

function Sheet({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center" role="dialog" aria-modal="true" aria-label={title}>
      <button type="button" aria-label="بستن" onClick={onClose} className="absolute inset-0 bg-black/50 backdrop-blur-sm" tabIndex={-1} />
      <div className="relative max-h-[92dvh] w-full max-w-xl overflow-y-auto rounded-t-[2rem] bg-surface p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] shadow-2xl ring-1 ring-line sm:rounded-[2rem] sm:p-7">
        <div className="mb-5 flex items-center justify-between gap-3">
          <h2 className="text-xl font-black">{title}</h2>
          <button type="button" onClick={onClose} aria-label="بستن" className="grid h-10 w-10 place-items-center rounded-full ring-1 ring-line-strong">
            <CloseIcon className="h-4 w-4" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function StaffForm({ member, onClose, onSaved }: { member: Staff | null; onClose: () => void; onSaved: () => void }) {
  const { call } = useAdmin();
  const [name, setName] = useState(member?.name ?? "");
  const [title, setTitle] = useState(member?.title ?? "");
  const [mobile, setMobile] = useState(member?.mobile ?? "");
  const [salary, setSalary] = useState(member ? Math.round(member.monthly_salary_irr / 10) : 0);
  const [note, setNote] = useState(member?.note ?? "");
  const [active, setActive] = useState(member?.active ?? true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body = { name, title, mobile, monthly_salary_toman: salary, note, active };
      if (member) await call(`/accounting/staff/${member.id}`, { method: "PUT", body });
      else await call("/accounting/staff", { method: "POST", body });
      onSaved();
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <Sheet title={member ? "ویرایش کارمند" : "کارمند تازه"} onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <Field label="نام و نام خانوادگی">
          <input className="field" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} required autoFocus />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="سمت (اختیاری)">
            <input className="field" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={80} placeholder="مثلاً مربی پیست" />
          </Field>
          <Field label="موبایل (اختیاری)">
            <input className="field" dir="ltr" value={mobile} onChange={(e) => setMobile(e.target.value)} maxLength={20} />
          </Field>
        </div>
        <MoneyInput label="حقوق ماهانه" value={salary} onChange={setSalary} />
        <Field label="یادداشت (اختیاری)">
          <input className="field" value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} />
        </Field>
        {member && (
          <label className="flex items-center gap-3 text-sm font-bold">
            <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} className="h-5 w-5" />
            هنوز همکاری می‌کند (اگر کنار رفته، برداریدش؛ سابقه‌اش می‌ماند)
          </label>
        )}
        {error && <Alert tone="error">{error}</Alert>}
        <button type="submit" disabled={busy || !name.trim()} className={buttonClasses("primary", "lg", "w-full")}>
          {busy ? <Spinner /> : "ذخیره"}
        </button>
      </form>
    </Sheet>
  );
}

function PaySheet({ staff, accounts, month, onClose, onPaid }: { staff: Staff; accounts: Account[]; month: JalaliMonth; onClose: () => void; onPaid: () => void }) {
  const { call } = useAdmin();
  const [kind, setKind] = useState<"salary" | "advance" | "bonus">("salary");
  const [amount, setAmount] = useState(Math.round(staff.remaining_irr / 10));
  const [wallet, setWallet] = useState<Wallet>("cash");
  const [day, setDay] = useState(() => {
    const today = currentBusinessDay();
    const [from, to] = monthBounds(month);
    return today >= from && today <= to ? today : to; // paying for a past month: dated at its end
  });
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const from = walletAccount(accounts, wallet);
    if (!from) return setError("حساب صندوق یا بانک پیدا نشد.");
    setBusy(true);
    setError(null);
    try {
      await call(`/accounting/staff/${staff.id}/pay`, { method: "POST", body: { kind, amount_toman: amount, date: day, paid_from_account_id: from.id, note } });
      onPaid();
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <Sheet title={`پرداخت به ${staff.name}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-5">
        <Segmented
          label="نوع پرداخت"
          options={[
            { id: "salary", label: "حقوق" },
            { id: "advance", label: "مساعده" },
            { id: "bonus", label: "پاداش" },
          ]}
          value={kind}
          onChange={(k) => {
            setKind(k);
            setAmount(k === "bonus" ? 0 : Math.round(staff.remaining_irr / 10));
          }}
        />
        <MoneyInput label="مبلغ" value={amount} onChange={setAmount} big autoFocus />
        {kind !== "bonus" && staff.remaining_irr > 0 && (
          <p className="-mt-3 text-xs text-fg-subtle">مانده‌ی حقوق این ماه: {toman(staff.remaining_irr)} تومان</p>
        )}
        <Segmented label="پرداخت از" options={(["cash", "bank"] as Wallet[]).map((w) => ({ id: w, label: WALLET_LABEL[w] }))} value={wallet} onChange={setWallet} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="تاریخ">
            <SingleDatePicker value={day} onChange={setDay} label="تاریخ پرداخت" />
          </Field>
          <Field label="توضیح (اختیاری)">
            <input className="field" value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} />
          </Field>
        </div>
        <p className="text-xs leading-6 text-fg-subtle">این پرداخت خودش در حسابداری به‌عنوان هزینه‌ی حقوق ثبت می‌شود و از {WALLET_LABEL[wallet]} کم می‌شود.</p>
        {error && <Alert tone="error">{error}</Alert>}
        <button type="submit" disabled={busy || amount <= 0} className={buttonClasses("primary", "lg", "w-full")}>
          {busy ? <Spinner /> : "ثبت پرداخت"}
        </button>
      </form>
    </Sheet>
  );
}
