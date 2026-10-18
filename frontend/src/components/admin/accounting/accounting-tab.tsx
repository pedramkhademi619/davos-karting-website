"use client";

import { useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { TabHeader } from "@/components/admin/admin-ui";
import { CashView } from "@/components/admin/accounting/cash-view";
import { CategoriesView } from "@/components/admin/accounting/categories-view";
import { DayBookView } from "@/components/admin/accounting/day-book-view";
import { EntrySheet, type EntryKind } from "@/components/admin/accounting/entry-sheet";
import { OverviewView } from "@/components/admin/accounting/overview-view";
import { ReportView } from "@/components/admin/accounting/report-view";
import { useAccountingData } from "@/components/admin/accounting/use-accounting-data";
import { buttonClasses } from "@/components/button-link";
import { PlusIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";

const SECTIONS = [
  { id: "overview", label: "خلاصه" },
  { id: "daybook", label: "دفتر روزانه" },
  { id: "cash", label: "صندوق" },
  { id: "report", label: "گزارش ماهانه" },
  { id: "categories", label: "دسته‌ها" },
] as const;

type SectionId = (typeof SECTIONS)[number]["id"];
type Sheet = { kind: EntryKind; amountToman?: number; refundsOwedIrr?: number };

/**
 * The money side of the track in plain words: ticket sales are booked by themselves; the owner records expenses and other
 * income in a few taps, counts the till, and reads one simple monthly report. Owner only.
 */
export function AccountingTab() {
  const { isOwner } = useAdmin();
  const { accounts, ready, error, reload } = useAccountingData();
  const [section, setSection] = useState<SectionId>("overview");
  const [version, setVersion] = useState(0);
  const [sheet, setSheet] = useState<Sheet | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const changed = () => {
    setVersion((v) => v + 1);
    void reload();
  };

  if (!isOwner) return <Alert tone="info">حسابداری فقط برای مالک در دسترس است.</Alert>;

  return (
    <div>
      <TabHeader
        title="حسابداری"
        lead="فروش بلیت خودش ثبت می‌شود؛ شما فقط خرج‌ها و درآمدهای دیگر را ثبت کنید. مبلغ‌ها به تومان است."
        actions={
          <>
            <button type="button" onClick={() => setSheet({ kind: "expense" })} className={buttonClasses("primary", "md")}>
              <PlusIcon className="h-4 w-4" /> ثبت هزینه
            </button>
            <button type="button" onClick={() => setSheet({ kind: "income" })} className={buttonClasses("dark", "md")}>
              <PlusIcon className="h-4 w-4" /> ثبت درآمد
            </button>
          </>
        }
      />
      <nav aria-label="بخش‌های حسابداری" className="-mx-1 mb-8 overflow-x-auto px-1 pb-2 pt-1">
        <div role="tablist" className="flex min-w-max gap-2 px-1">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              role="tab"
              aria-selected={section === s.id}
              onClick={() => setSection(s.id)}
              className={`rounded-full px-4 py-2.5 text-sm font-extrabold ring-1 transition-colors ${section === s.id ? "bg-ink text-white ring-ink" : "bg-surface text-fg-muted ring-line-strong hover:text-fg"}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </nav>

      {saved && (
        <Alert tone="success" className="mb-6">
          {saved}
        </Alert>
      )}
      {error && (
        <Alert tone="error" className="mb-6">
          {error}
        </Alert>
      )}
      {!ready ? (
        <Spinner className="h-8 w-8" />
      ) : (
        <>
          <div key={section === "daybook" ? section : `${section}-${version}`}>
            {section === "overview" && <OverviewView onPayRefunds={(owed) => setSheet({ kind: "refund", amountToman: Math.floor(owed / 10), refundsOwedIrr: owed })} />}
            {section === "daybook" && <DayBookView accounts={accounts} version={version} onChanged={changed} />}
            {section === "cash" && <CashView onChanged={changed} />}
            {section === "report" && <ReportView />}
            {section === "categories" && <CategoriesView accounts={accounts} onChanged={changed} />}
          </div>
          {sheet && (
            <EntrySheet
              accounts={accounts}
              kind={sheet.kind}
              amountToman={sheet.amountToman}
              refundsOwedIrr={sheet.refundsOwedIrr}
              onClose={() => setSheet(null)}
              onCategoriesChanged={() => void reload()}
              onSaved={(message) => {
                setSheet(null);
                setSaved(message);
                changed();
              }}
            />
          )}
        </>
      )}
    </div>
  );
}
