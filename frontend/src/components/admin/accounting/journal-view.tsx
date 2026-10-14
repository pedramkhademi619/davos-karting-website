"use client";

import { Fragment, useCallback, useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Pager, Table, cell } from "@/components/admin/admin-ui";
import { SingleDatePicker } from "@/components/admin/date-picker-field";
import { AccountSelect, Field, MoneyInput } from "@/components/admin/accounting/accounting-fields";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { SOURCE_LABEL, downloadCsv, csvToman, toman, tomanOrDash, type Account, type Entry, type Vendor } from "@/lib/accounting";
import { fa, toLatinDigits } from "@/lib/format";
import { currentBusinessDay, isoToJalali } from "@/lib/jalali";

const LIMIT = 30;
type Page = { items: Entry[]; total: number };
type DraftLine = { account: string; debit: number; credit: number; memo: string; vendor: string };

const blankLine = (): DraftLine => ({ account: "", debit: 0, credit: 0, memo: "", vendor: "" });

/** The journal book (دفتر روزنامه): every entry, with its lines, a way to cancel one, and manual entries. */
export function JournalView({ accounts, vendors, onChanged }: { accounts: Account[]; vendors: Vendor[]; onChanged: () => void }) {
  const { call } = useAdmin();
  const [page, setPage] = useState<Page | null>(null);
  const [offset, setOffset] = useState(0);
  const [text, setText] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [account, setAccount] = useState("");
  const [source, setSource] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [writing, setWriting] = useState(false);
  const [version, setVersion] = useState(0);

  const load = useCallback(async () => {
    try {
      setPage(await call<Page>("/accounting/journal", { query: { q: submitted, account_id: account, source, offset, limit: LIMIT } }));
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [call, submitted, account, source, offset]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reloads when a filter or the page changes
    void load();
  }, [load, version]);

  async function reverse(entry: Entry) {
    const reason = window.prompt(`دلیل ابطال سند ${fa(entry.number)} را بنویسید:`, "");
    if (reason === null) return;
    try {
      await call<Entry>(`/accounting/journal/${entry.id}/reverse`, { method: "POST", body: { reason } });
      setVersion((v) => v + 1);
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  function exportCsv() {
    if (!page) return;
    downloadCsv(
      "journal",
      ["شماره سند", "سال مالی", "تاریخ", "شرح", "نوع", "حساب", "بدهکار (تومان)", "بستانکار (تومان)"],
      page.items.flatMap((e) => e.lines.map((l) => [e.number, e.fiscal_year, isoToJalali(e.date), e.description, SOURCE_LABEL[e.source] ?? e.source, `${l.account_code} ${l.account_name}`, csvToman(l.debit_irr), csvToman(l.credit_irr)])),
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end gap-3">
        <form
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            setOffset(0);
            setSubmitted(toLatinDigits(text.trim()));
          }}
          className="flex flex-wrap items-end gap-3"
        >
          <input className="field h-11 w-56" placeholder="شماره سند یا شرح" aria-label="جستجوی سند" value={text} onChange={(e) => setText(e.target.value)} />
          <select className="field h-11 w-60" value={account} aria-label="فیلتر حساب" onChange={(e) => { setOffset(0); setAccount(e.target.value); }}>
            <option value="">همه حساب‌ها</option>
            {accounts.filter((a) => !a.is_group).map((a) => (
              <option key={a.id} value={a.id}>
                {fa(a.code)} · {a.name}
              </option>
            ))}
          </select>
          <select className="field h-11 w-48" value={source} aria-label="فیلتر نوع سند" onChange={(e) => { setOffset(0); setSource(e.target.value); }}>
            <option value="">همه انواع</option>
            {Object.entries(SOURCE_LABEL).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
          <button type="submit" className={buttonClasses("dark", "sm", "h-11")}>
            جستجو
          </button>
        </form>
        <button type="button" onClick={exportCsv} className={buttonClasses("ghost", "sm", "h-11")}>
          خروجی CSV
        </button>
        <button type="button" onClick={() => setWriting((v) => !v)} className={buttonClasses("primary", "sm", "h-11 mr-auto")}>
          {writing ? "بستن فرم" : "سند دستی جدید"}
        </button>
      </div>

      {writing && <ManualEntry accounts={accounts} vendors={vendors} onPosted={() => { setWriting(false); setVersion((v) => v + 1); onChanged(); }} />}
      {error && <Alert tone="error">{error}</Alert>}

      {!page ? (
        <Spinner className="h-8 w-8" />
      ) : (
        <>
          <Table head={["شماره", "تاریخ", "شرح", "نوع", "مبلغ (تومان)", "وضعیت", ""]} empty={page.items.length === 0}>
            {page.items.map((entry) => (
              <Fragment key={entry.id}>
                <tr className={entry.status === "reversed" ? "text-fg-subtle line-through decoration-1" : ""}>
                  <td className={`${cell} font-black`}>{fa(entry.number)}<span className="mr-1 text-xs font-normal text-fg-subtle">/{fa(entry.fiscal_year)}</span></td>
                  <td className={cell}>{fa(isoToJalali(entry.date))}</td>
                  <td className={`${cell} max-w-[22rem] truncate`} title={entry.description}>{entry.description}</td>
                  <td className={cell}>{SOURCE_LABEL[entry.source] ?? entry.source}</td>
                  <td className={cell}>{toman(entry.total_irr)}</td>
                  <td className={cell}>{entry.status === "reversed" ? "ابطال‌شده" : "ثبت‌شده"}</td>
                  <td className={cell}>
                    <button type="button" className="font-bold underline underline-offset-4" onClick={() => setOpenId(openId === entry.id ? null : entry.id)}>
                      {openId === entry.id ? "بستن" : "جزئیات"}
                    </button>
                  </td>
                </tr>
                {openId === entry.id && (
                  <tr>
                    <td colSpan={7} className="bg-surface-2 px-4 py-4">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-right text-xs text-fg-muted">
                            <th className="py-1">حساب</th>
                            <th className="py-1">تامین‌کننده</th>
                            <th className="py-1">شرح</th>
                            <th className="py-1">بدهکار</th>
                            <th className="py-1">بستانکار</th>
                          </tr>
                        </thead>
                        <tbody>
                          {entry.lines.map((line, index) => (
                            <tr key={index} className="border-t border-line">
                              <td className="py-1.5 font-bold">{fa(line.account_code)} · {line.account_name}</td>
                              <td className="py-1.5">{line.vendor_name || "—"}</td>
                              <td className="py-1.5 text-fg-muted">{line.memo}</td>
                              <td className="py-1.5">{tomanOrDash(line.debit_irr)}</td>
                              <td className="py-1.5">{tomanOrDash(line.credit_irr)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <p className="mt-3 text-xs text-fg-subtle">ثبت‌کننده: {entry.created_by}</p>
                      {entry.status === "posted" && entry.source !== "reversal" && entry.source !== "closing" && (
                        <button type="button" onClick={() => reverse(entry)} className={buttonClasses("signal", "sm", "mt-3")}>
                          ابطال سند
                        </button>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </Table>
          <Pager offset={offset} limit={LIMIT} total={page.total} onChange={setOffset} />
        </>
      )}
    </div>
  );
}

function ManualEntry({ accounts, vendors, onPosted }: { accounts: Account[]; vendors: Vendor[]; onPosted: () => void }) {
  const { call } = useAdmin();
  const [day, setDay] = useState(currentBusinessDay());
  const [description, setDescription] = useState("");
  const [opening, setOpening] = useState(false);
  const [lines, setLines] = useState<DraftLine[]>([blankLine(), blankLine()]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debit = lines.reduce((s, l) => s + l.debit, 0);
  const credit = lines.reduce((s, l) => s + l.credit, 0);
  const balanced = debit === credit && debit > 0;
  const set = (index: number, patch: Partial<DraftLine>) => setLines((current) => current.map((l, i) => (i === index ? { ...l, ...patch } : l)));

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await call<Entry>("/accounting/journal", {
        method: "POST",
        body: {
          date: day,
          description,
          opening,
          lines: lines
            .filter((l) => l.account && (l.debit || l.credit))
            .map((l) => ({ account_id: l.account, debit_toman: l.debit, credit_toman: l.credit, memo: l.memo, vendor_id: l.vendor || null })),
        },
      });
      onPosted();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="سند حسابداری دستی">
      <form onSubmit={submit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="تاریخ">
            <SingleDatePicker value={day} onChange={setDay} label="تاریخ سند" />
          </Field>
          <div className="sm:col-span-2">
            <Field label="شرح سند">
              <input className="field" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={300} required />
            </Field>
          </div>
        </div>
        <label className="flex items-center gap-3 text-sm font-bold">
          <input type="checkbox" className="h-5 w-5 accent-[#0c0d10]" checked={opening} onChange={(e) => setOpening(e.target.checked)} />
          این سند افتتاحیه است (موجودی‌های اول کار)
        </label>
        <div className="space-y-3">
          {lines.map((line, index) => (
            <div key={index} className="grid gap-3 rounded-2xl border border-line p-3 lg:grid-cols-12">
              <div className="lg:col-span-4">
                <AccountSelect label="حساب" accounts={accounts} value={line.account} onChange={(id) => set(index, { account: id })} />
              </div>
              <div className="lg:col-span-2">
                <MoneyInput label="بدهکار" value={line.debit} onChange={(v) => set(index, { debit: v, credit: v ? 0 : line.credit })} />
              </div>
              <div className="lg:col-span-2">
                <MoneyInput label="بستانکار" value={line.credit} onChange={(v) => set(index, { credit: v, debit: v ? 0 : line.debit })} />
              </div>
              <div className="lg:col-span-3">
                <Field label="شرح / تامین‌کننده">
                  <input className="field" value={line.memo} onChange={(e) => set(index, { memo: e.target.value })} maxLength={300} />
                </Field>
                <select className="field mt-2" value={line.vendor} onChange={(e) => set(index, { vendor: e.target.value })} aria-label="تامین‌کننده این سطر">
                  <option value="">بدون تامین‌کننده</option>
                  {vendors.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-end lg:col-span-1">
                {lines.length > 2 && (
                  <button type="button" onClick={() => setLines((c) => c.filter((_, i) => i !== index))} className="h-11 w-full rounded-full border border-line-strong text-sm font-bold hover:bg-surface-2">
                    حذف
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <button type="button" onClick={() => setLines((c) => [...c, blankLine()])} className={buttonClasses("ghost", "sm")}>
            + سطر جدید
          </button>
          <p className={`text-sm font-bold ${balanced ? "text-go" : "text-signal"}`}>
            جمع بدهکار: {toman(debit * 10)} · جمع بستانکار: {toman(credit * 10)} {balanced ? "· تراز است" : debit === credit ? "" : `· اختلاف: ${toman(Math.abs(debit - credit) * 10)}`}
          </p>
        </div>
        {error && <Alert tone="error">{error}</Alert>}
        <button type="submit" disabled={busy || !balanced} className={buttonClasses("primary", "md")}>
          {busy ? <Spinner /> : "ثبت سند"}
        </button>
      </form>
    </Card>
  );
}
