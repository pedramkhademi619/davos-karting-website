"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { OtpLogin } from "@/components/auth/otp-login";
import { buttonClasses } from "@/components/button-link";
import { LogoutIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { site } from "@/content/site";
import { api } from "@/lib/api";
import { fa, mobile } from "@/lib/format";
import type { Me } from "@/lib/types";
import { useCustomer } from "@/lib/use-customer";
import { AccountHelp } from "./account-help";
import { AccountOverview } from "./account-overview";
import { AccountPayments } from "./account-payments";
import { AccountProfile } from "./account-profile";
import { AccountSecurity } from "./account-security";
import { AccountTickets } from "./account-tickets";
import { isOpenTicket, useAccountData } from "./use-account-data";

const TABS = [
  { id: "overview", label: "نمای کلی" },
  { id: "tickets", label: "بلیت‌ها" },
  { id: "payments", label: "پرداخت‌ها" },
  { id: "profile", label: "اطلاعات من" },
  { id: "security", label: "امنیت و دستگاه‌ها" },
  { id: "help", label: "راهنما" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const isTab = (value: string): value is TabId => TABS.some((t) => t.id === value);

/** The customer's account: overview, tickets, payments, profile, signed-in devices and venue help, plus sign-out. */
export function AccountApp() {
  const { state, signedIn, signedOut } = useCustomer();

  if (state.status === "loading") {
    return (
      <div className="grid min-h-[30vh] place-items-center">
        <Spinner className="h-9 w-9" />
      </div>
    );
  }
  if (state.status === "guest") {
    return (
      <div className="panel mx-auto max-w-md p-7 md:p-9">
        <OtpLogin onSignedIn={signedIn} title="برای دیدن بلیت‌ها وارد شوید" />
      </div>
    );
  }
  return <SignedInAccount me={state.me} onSignedOut={signedOut} />;
}

function SignedInAccount({ me, onSignedOut }: { me: Me; onSignedOut: () => void }) {
  const { data, error, reload, setProfile } = useAccountData(onSignedOut);
  const [tab, setTab] = useState<TabId>("overview");

  useEffect(() => {
    const fromHash = () => {
      const id = window.location.hash.slice(1);
      if (isTab(id)) setTab(id);
    };
    fromHash();
    window.addEventListener("hashchange", fromHash);
    return () => window.removeEventListener("hashchange", fromHash);
  }, []);

  const select = useCallback((id: TabId) => {
    setTab(id);
    window.history.replaceState(null, "", `#${id}`);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api<void>("/auth/logout", { method: "POST", csrf: me.csrf_token });
    } finally {
      onSignedOut();
    }
  }, [me.csrf_token, onSignedOut]);

  if (error) return <Alert tone="error">{error}</Alert>;
  if (!data) {
    return (
      <div className="grid min-h-[30vh] place-items-center">
        <Spinner className="h-9 w-9" />
      </div>
    );
  }

  const { profile, reservations, payments } = data;
  const open = reservations.filter(isOpenTicket).length;
  const name = profile.full_name.trim();

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-center justify-between gap-5">
        <div className="flex items-center gap-4">
          <span
            aria-hidden="true"
            className="race-number grid h-14 w-14 place-items-center rounded-full bg-accent text-2xl font-black text-ink"
          >
            {name ? name.charAt(0) : "؟"}
          </span>
          <div>
            <p className="text-xl font-black">{name || "مشتری گرامی"}</p>
            <p className="text-sm text-fg-muted" dir="ltr" style={{ textAlign: "right" }}>
              {mobile(profile.mobile)}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href={site.booking.href} className={buttonClasses("primary", "sm")}>
            رزرو جدید
          </Link>
          <button type="button" onClick={logout} className={buttonClasses("ghost", "sm")}>
            <LogoutIcon className="h-4 w-4" />
            خروج
          </button>
        </div>
      </header>

      <nav aria-label="بخش‌های حساب" className="-mx-1 overflow-x-auto pb-1">
        <div role="tablist" className="flex min-w-max gap-2 px-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              id={`tab-${t.id}`}
              aria-selected={tab === t.id}
              aria-controls={`panel-${t.id}`}
              onClick={() => select(t.id)}
              className={`rounded-full px-5 py-2.5 text-sm font-extrabold ring-1 transition-colors ${
                tab === t.id ? "bg-ink text-white ring-ink" : "bg-surface text-fg-muted ring-line-strong hover:text-fg"
              }`}
            >
              {t.label}
              {t.id === "tickets" && open > 0 && (
                <span className="mr-2 rounded-full bg-accent px-2 py-0.5 text-xs font-black text-ink">{fa(open)}</span>
              )}
            </button>
          ))}
        </div>
      </nav>

      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
        {tab === "overview" && <AccountOverview profile={profile} tickets={reservations} payments={payments} goTo={select} />}
        {tab === "tickets" && <AccountTickets tickets={reservations} payments={payments} me={me} onChanged={reload} />}
        {tab === "payments" && <AccountPayments payments={payments} tickets={reservations} />}
        {tab === "profile" && <AccountProfile profile={profile} me={me} onSaved={setProfile} />}
        {tab === "security" && <AccountSecurity me={me} onSignedOut={onSignedOut} onLogout={logout} />}
        {tab === "help" && <AccountHelp />}
      </div>
    </div>
  );
}
