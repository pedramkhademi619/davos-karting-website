"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { MonthStepper } from "@/components/admin/accounting/month-stepper";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import {
  DAY_BOOK_SOURCES,
  monthBounds,
  monthOf,
  toman,
  viewEntry,
  type Account,
  type Entry,
  type EntryView,
  type JalaliMonth,
  type SalesDay,
  type SalesReport,
} from "@/lib/accounting";
import { fa } from "@/lib/format";
import { currentBusinessDay, isoToJalaliParts, JALALI_MONTHS, weekdayIndex } from "@/lib/jalali";

const PAGE = 200;
const WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"];
const DELETABLE = new Set(["expense", "income", "transfer", "payroll", "vendor_payment", "manual"]);

function dayTitle(iso: string): string {
  const { jd, jm } = isoToJalaliParts(iso);
  return `${WEEKDAYS[weekdayIndex(iso)]} ${fa(jd)} ${JALALI_MONTHS[jm - 1]}`;
}

/**
 * The month day by day: ticket sales as one line per day (they are booked automatically), then everything recorded by
 * hand that day. A wrong entry is deleted here (the books keep a reversing entry, so nothing silently disappears).
 */
export function DayBookView({ accounts, version, onChanged }: { accounts: Account[]; version: number; onChanged: () => void }) {
  const { call } = useAdmin();
  const [month, setMonth] = useState<JalaliMonth>(() => monthOf(currentBusinessDay()));
  const [entries, setEntries] = useState<Entry[] | null>(null);
  const [sales, setSales] = useState<SalesDay[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const byId = useMemo(() => new Map(accounts.map((a) => [a.id, a])), [accounts]);

  const load = useCallback(async () => {
    const [from, to] = monthBounds(month);
    setEntries(null);
    try {
      const all: Entry[] = [];
      for (let offset = 0; ; offset += PAGE) {
        const page = await call<{ items: Entry[]; total: number }>("/accounting/journal", {
          query: { from, to, source: DAY_BOOK_SOURCES.join(","), offset, limit: PAGE },
        });
        all.push(...page.items);
        if (offset + PAGE >= page.total) break;
      }
      const report = await call<SalesReport>("/accounting/reports/sales", { query: { from, to } });
      setEntries(all);
      setSales(report.days);
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
      setEntries([]);
    }
  }, [call, month]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reloads when the month or the books change
    void load();
  }, [load, version]);

  async function remove(entry: Entry) {
    setBusy(true);
    try {
      await call(`/accounting/journal/${entry.id}/reverse`, { method: "POST", body: { reason: "حذف از دفتر روزانه" } });
      setConfirming(null);
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const days = useMemo(() => {
    const map = new Map<string, { sales?: SalesDay; entries: Entry[] }>();
    for (const day of sales) if (day.received_irr) map.set(day.date, { sales: day, entries: [] });
    for (const entry of entries ?? []) {
      if (entry.source === "cash_close" && entry.total_irr === 0) continue;
      const slot = map.get(entry.date) ?? { entries: [] };
      slot.entries.push(entry);
      map.set(entry.date, slot);
    }
    return [...map.entries()].sort(([a], [b]) => b.localeCompare(a));
  }, [entries, sales]);

  return (
    <div className="space-y-5">
      <MonthStepper month={month} onChange={setMonth} />
      {error && <Alert tone="error">{error}</Alert>}
      {entries === null ? (
        <Spinner className="h-8 w-8" />
      ) : days.length === 0 ? (
        <p className="panel p-8 text-center text-fg-muted">در این ماه چیزی ثبت نشده است.</p>
      ) : (
        days.map(([date, day]) => (
          <section key={date} className="panel overflow-hidden">
            <h3 className="flex items-center justify-between gap-3 border-b border-line bg-surface-2 px-5 py-3 text-sm font-black">
              <span>{dayTitle(date)}</span>
            </h3>
            <ul className="divide-y divide-line">
              {day.sales && (
                <li className="flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-3.5">
                  <Arrow direction="in" />
                  <div className="min-w-0 flex-1">
                    <p className="font-bold">فروش بلیت</p>
                    <p className="text-xs text-fg-subtle">
                      {[
                        day.sales.online_irr ? `آنلاین ${toman(day.sales.online_irr)}` : null,
                        day.sales.cash_irr ? `نقد ${toman(day.sales.cash_irr)}` : null,
                        day.sales.card_irr ? `کارت ${toman(day.sales.card_irr)}` : null,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  </div>
                  <Amount view={{ direction: "in", amount_irr: day.sales.received_irr }} />
                </li>
              )}
              {day.entries.map((entry) => {
                const view = viewEntry(entry, byId);
                const reversed = entry.status === "reversed";
                return (
                  <li key={entry.id} className={`flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-3.5 ${reversed ? "opacity-50" : ""}`}>
                    <Arrow direction={view.direction} />
                    <div className="min-w-0 flex-1">
                      <p className={`font-bold ${reversed ? "line-through" : ""}`}>{view.title}</p>
                      <p className="text-xs text-fg-subtle">
                        {[view.category !== view.title ? view.category : null, view.wallet, reversed ? "حذف شده" : null].filter(Boolean).join(" · ")}
                      </p>
                    </div>
                    <Amount view={view} />
                    {!reversed && DELETABLE.has(entry.source) && (
                      <div className="flex w-full justify-end gap-2 sm:w-auto">
                        {confirming === entry.id ? (
                          <>
                            <button type="button" disabled={busy} onClick={() => remove(entry)} className="rounded-full bg-signal px-3 py-1.5 text-xs font-black text-white">
                              {busy ? <Spinner /> : "بله، حذف"}
                            </button>
                            <button type="button" onClick={() => setConfirming(null)} className="rounded-full px-3 py-1.5 text-xs font-bold ring-1 ring-line-strong">
                              نه
                            </button>
                          </>
                        ) : (
                          <button type="button" onClick={() => setConfirming(entry.id)} className="rounded-full px-3 py-1.5 text-xs font-bold text-fg-muted ring-1 ring-line-strong hover:text-signal">
                            حذف
                          </button>
                        )}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </section>
        ))
      )}
    </div>
  );
}

function Arrow({ direction }: { direction: EntryView["direction"] }) {
  const style = {
    in: ["↓", "bg-go/15 text-go"],
    out: ["↑", "bg-signal/15 text-signal"],
    move: ["⇄", "bg-surface-2 text-fg-muted"],
    other: ["•", "bg-surface-2 text-fg-muted"],
  }[direction];
  return (
    <span aria-hidden="true" className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-lg font-black ${style[1]}`}>
      {style[0]}
    </span>
  );
}

function Amount({ view }: { view: Pick<EntryView, "direction" | "amount_irr"> }) {
  const sign = view.direction === "in" ? "+" : view.direction === "out" ? "−" : "";
  const tone = view.direction === "in" ? "text-go" : view.direction === "out" ? "text-signal" : "text-fg-muted";
  return (
    <span className={`shrink-0 text-left font-black tabular-nums ${tone}`} dir="ltr">
      {sign}
      {toman(view.amount_irr)}
    </span>
  );
}
