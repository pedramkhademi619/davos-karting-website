"use client";

import { useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { TabHeader } from "@/components/admin/admin-ui";
import { AccountingDashboardView } from "@/components/admin/accounting/accounting-dashboard";
import { AccountingSettingsView } from "@/components/admin/accounting/accounting-settings-view";
import { AssetsView } from "@/components/admin/accounting/assets-view";
import { BudgetView } from "@/components/admin/accounting/budget-view";
import { CashView } from "@/components/admin/accounting/cash-view";
import { ChartView } from "@/components/admin/accounting/chart-view";
import { JournalView } from "@/components/admin/accounting/journal-view";
import { QuickEntry } from "@/components/admin/accounting/quick-entry";
import { ReportsView } from "@/components/admin/accounting/reports-view";
import { useAccountingData } from "@/components/admin/accounting/use-accounting-data";
import { VendorsView } from "@/components/admin/accounting/vendors-view";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";

const SECTIONS = [
  { id: "dashboard", label: "داشبورد مالی" },
  { id: "entry", label: "ثبت سریع" },
  { id: "journal", label: "اسناد (دفتر روزنامه)" },
  { id: "reports", label: "گزارش‌ها" },
  { id: "vendors", label: "تامین‌کنندگان" },
  { id: "assets", label: "دارایی‌ها و استهلاک" },
  { id: "cash", label: "صندوق" },
  { id: "budget", label: "بودجه" },
  { id: "chart", label: "سرفصل‌های حساب" },
  { id: "settings", label: "تنظیمات" },
] as const;

type SectionId = (typeof SECTIONS)[number]["id"];

/** Double-entry accounting for the business: bookkeeping, statements, suppliers, assets, budgets and year-end. Owner only. */
export function AccountingTab() {
  const { isOwner } = useAdmin();
  const { accounts, vendors, ready, error, reload } = useAccountingData();
  const [section, setSection] = useState<SectionId>("dashboard");
  const [version, setVersion] = useState(0);
  const changed = () => {
    setVersion((v) => v + 1);
    void reload();
  };

  if (!isOwner) return <Alert tone="info">حسابداری فقط برای مالک در دسترس است.</Alert>;

  return (
    <div>
      <TabHeader
        title="حسابداری"
        lead="دفاتر مالی مجموعه: فروش بلیت‌ها خودکار ثبت می‌شود و هزینه‌ها، دارایی‌ها و بدهی‌ها را اینجا اضافه می‌کنید. همه گزارش‌ها از همین اسناد ساخته می‌شوند و مبلغ‌ها به تومان است."
      />
      <nav aria-label="بخش‌های حسابداری" className="-mx-1 mb-8 overflow-x-auto pb-1">
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

      {error && <Alert tone="error" className="mb-6">{error}</Alert>}
      {!ready ? (
        <Spinner className="h-8 w-8" />
      ) : (
        <div key={`${section}-${version}`}>
          {section === "dashboard" && <AccountingDashboardView />}
          {section === "entry" && <QuickEntry accounts={accounts} vendors={vendors} onDone={changed} />}
          {section === "journal" && <JournalView accounts={accounts} vendors={vendors} onChanged={changed} />}
          {section === "reports" && <ReportsView accounts={accounts} vendors={vendors} />}
          {section === "vendors" && <VendorsView vendors={vendors} onChanged={changed} />}
          {section === "assets" && <AssetsView accounts={accounts} vendors={vendors} onChanged={changed} />}
          {section === "cash" && <CashView onChanged={changed} />}
          {section === "budget" && <BudgetView accounts={accounts} />}
          {section === "chart" && <ChartView accounts={accounts} onChanged={changed} />}
          {section === "settings" && <AccountingSettingsView onChanged={changed} />}
        </div>
      )}
    </div>
  );
}
