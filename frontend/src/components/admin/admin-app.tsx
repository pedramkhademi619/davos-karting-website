"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type ComponentType, type FormEvent, type SVGProps } from "react";
import { AdminSessionContext, makeSession } from "@/components/admin/admin-session";
import { CustomersTab } from "@/components/admin/customers-tab";
import { DashboardTab } from "@/components/admin/dashboard-tab";
import { PaymentsTab } from "@/components/admin/payments-tab";
import { ReservationsTab } from "@/components/admin/reservations-tab";
import { SettingsTab } from "@/components/admin/settings-tab";
import { SmsTab } from "@/components/admin/sms-tab";
import { UsersTab } from "@/components/admin/users-tab";
import { buttonClasses } from "@/components/button-link";
import { CalendarIcon, CardIcon, GaugeIcon, LogoutIcon, SettingsIcon, SmsIcon, UserIcon, UsersIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { SpeedLines } from "@/components/speed-lines";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { api, errorMessage } from "@/lib/api";
import type { AdminMe } from "@/lib/types";

type TabKey = "dashboard" | "reservations" | "customers" | "payments" | "sms" | "settings" | "users";

const TABS: { key: TabKey; label: string; icon: ComponentType<SVGProps<SVGSVGElement>>; ownerOnly?: boolean }[] = [
  { key: "dashboard", label: "داشبورد", icon: GaugeIcon },
  { key: "reservations", label: "رزروها و سانس‌ها", icon: CalendarIcon },
  { key: "customers", label: "مشتریان", icon: UserIcon },
  { key: "payments", label: "پرداخت‌ها", icon: CardIcon },
  { key: "sms", label: "پنل پیامک", icon: SmsIcon },
  { key: "settings", label: "تنظیمات و قیمت‌ها", icon: SettingsIcon },
  { key: "users", label: "کاربران پنل", icon: UsersIcon },
];

/** The staff panel: sign-in, then one screen per area. The API enforces every permission; the UI only mirrors it. */
export function AdminApp() {
  const [me, setMe] = useState<AdminMe | null>(null);
  const [checking, setChecking] = useState(true);
  const [tab, setTab] = useState<TabKey>("dashboard");

  useEffect(() => {
    let cancelled = false;
    api<AdminMe>("/admin/auth/me")
      .then((result) => !cancelled && setMe(result))
      .catch(() => undefined)
      .finally(() => !cancelled && setChecking(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const signOut = useCallback(() => setMe(null), []);
  const session = useMemo(() => (me ? makeSession(me, signOut) : null), [me, signOut]);

  async function logout() {
    if (!session) return;
    try {
      await session.call<void>("/auth/logout", { method: "POST" });
    } catch {
      // the cookie may already be gone; either way the panel signs out
    }
    signOut();
  }

  if (checking) {
    return (
      <div className="grid min-h-svh place-items-center">
        <Spinner className="h-9 w-9" />
      </div>
    );
  }
  if (!session) return <AdminLogin onSignedIn={setMe} />;

  return (
    <AdminSessionContext.Provider value={session}>
      <div className="flex min-h-svh flex-col lg:flex-row">
        <aside className="carbon relative shrink-0 overflow-hidden lg:sticky lg:top-0 lg:h-svh lg:w-72">
          <div className="flex items-center justify-between gap-4 p-5 lg:block">
            <Link href="/" className="rounded-xl">
              <Logo tone="light" />
            </Link>
            <p className="text-xs text-on-carbon-muted lg:mt-6">
              {session.me.display_name || session.me.username} · {session.isOwner ? "مالک" : "کارمند"}
            </p>
          </div>
          <nav aria-label="بخش‌های پنل" className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:px-3">
            {TABS.map(({ key, label, icon: IconComponent }) => (
              <button
                key={key}
                type="button"
                onClick={() => setTab(key)}
                aria-current={tab === key ? "page" : undefined}
                className={`flex shrink-0 items-center gap-3 rounded-2xl px-4 py-3 text-sm font-bold transition-colors ${
                  tab === key ? "bg-accent text-ink" : "text-on-carbon-muted hover:bg-white/5 hover:text-on-carbon"
                }`}
              >
                <IconComponent className="h-5 w-5" />
                {label}
              </button>
            ))}
            <button
              type="button"
              onClick={logout}
              className="flex shrink-0 items-center gap-3 rounded-2xl px-4 py-3 text-sm font-bold text-on-carbon-muted transition-colors hover:bg-white/5 hover:text-signal lg:mt-4"
            >
              <LogoutIcon className="h-5 w-5" />
              خروج
            </button>
          </nav>
        </aside>

        <main className="min-w-0 flex-1 p-4 md:p-8">
          {tab === "dashboard" && <DashboardTab onOpen={setTab} />}
          {tab === "reservations" && <ReservationsTab />}
          {tab === "customers" && <CustomersTab />}
          {tab === "payments" && <PaymentsTab />}
          {tab === "sms" && <SmsTab />}
          {tab === "settings" && <SettingsTab />}
          {tab === "users" && <UsersTab />}
        </main>
      </div>
    </AdminSessionContext.Provider>
  );
}

function AdminLogin({ onSignedIn }: { onSignedIn: (me: AdminMe) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onSignedIn(await api<AdminMe>("/admin/auth/login", { method: "POST", body: { username: username.trim(), password } }));
    } catch (err) {
      setError(errorMessage(err));
      setPassword("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="carbon relative grid min-h-svh place-items-center overflow-hidden p-5">
      <SpeedLines />
      <form onSubmit={submit} className="relative w-full max-w-sm rounded-[2rem] bg-carbon-2/90 p-8 ring-1 ring-white/10 backdrop-blur">
        <Logo tone="light" />
        <h1 className="mt-8 text-2xl font-black">ورود به پنل مدیریت</h1>
        <div className="mt-6 space-y-4">
          <div>
            <label htmlFor="admin-username" className="label text-on-carbon-muted">
              نام کاربری
            </label>
            <input
              id="admin-username"
              dir="ltr"
              className="field field-dark"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label htmlFor="admin-password" className="label text-on-carbon-muted">
              رمز عبور
            </label>
            <input
              id="admin-password"
              type="password"
              dir="ltr"
              className="field field-dark"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {error && <Alert tone="error">{error}</Alert>}
          <button type="submit" disabled={busy} className={buttonClasses("primary", "lg", "w-full")}>
            {busy ? <Spinner /> : "ورود"}
          </button>
        </div>
        <p className="mt-6 text-xs leading-6 text-on-carbon-muted">پس از چند تلاش ناموفق، حساب برای مدتی قفل می‌شود.</p>
      </form>
    </div>
  );
}
