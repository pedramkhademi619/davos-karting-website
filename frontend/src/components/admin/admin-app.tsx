"use client";

import { PasswordInput } from "@/components/ui/password-input";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { AdminSessionContext, makeSession } from "@/components/admin/admin-session";
import { SECTIONS, sectionAllowed, type SectionKey } from "@/components/admin/admin-sections";
import { buttonClasses } from "@/components/button-link";
import { LogoutIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { SpeedLines } from "@/components/speed-lines";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { api, errorMessage } from "@/lib/api";
import { SITE_HOME } from "@/lib/urls";
import type { AdminMe } from "@/lib/types";
import { PageSkeleton } from "@/components/ui/skeleton";

/** The staff panel: sign-in, then one screen per area. The API enforces every permission; the UI only mirrors it. */
export function AdminApp() {
  const [me, setMe] = useState<AdminMe | null>(null);
  const [checking, setChecking] = useState(true);
  const [tab, setTab] = useState<SectionKey | null>(null);

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
        <PageSkeleton variant="page" />
      </div>
    );
  }
  if (!session) return <AdminLogin onSignedIn={setMe} />;

  const allowed = SECTIONS.filter((section) => sectionAllowed(section, session.can, session.isOwner));
  const shown = tab ?? allowed[0]?.key ?? null;
  const current = allowed.find((section) => section.key === shown) ?? null;

  return (
    <AdminSessionContext.Provider value={session}>
      <div className="flex min-h-svh flex-col lg:flex-row">
        <aside className="carbon relative shrink-0 overflow-hidden lg:sticky lg:top-0 lg:h-svh lg:w-72">
          <div className="flex items-center justify-between gap-4 p-5 lg:block">
            <Link href={SITE_HOME} className="rounded-xl">
              <Logo tone="light" />
            </Link>
            <p className="text-xs text-on-carbon-muted lg:mt-6">
              {session.me.display_name || session.me.username} · {session.isOwner ? "مالک" : "کارمند"}
            </p>
          </div>
          <nav aria-label="بخش‌های پنل" className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:px-3">
            {allowed.map(({ key, label, icon: IconComponent }) => (
              <button
                key={key}
                type="button"
                onClick={() => setTab(key)}
                aria-current={shown === key ? "page" : undefined}
                className={`flex shrink-0 items-center gap-3 rounded-2xl px-4 py-3 text-sm font-bold transition-colors ${
                  shown === key ? "bg-accent text-ink" : "text-on-carbon-muted hover:bg-white/5 hover:text-on-carbon"
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
          {current ? (
            <current.Component onOpen={setTab} />
          ) : (
            <AccessDenied wanted={SECTIONS.find((section) => section.key === tab)?.label} onGoHome={() => setTab(allowed[0]?.key ?? null)} />
          )}
        </main>
      </div>
    </AdminSessionContext.Provider>
  );
}

/** Shown when a section is opened without permission (the menu hides such sections, so this is a direct visit). */
function AccessDenied({ wanted, onGoHome }: { wanted?: string; onGoHome: () => void }) {
  return (
    <div className="panel mx-auto mt-10 max-w-xl p-8 text-center">
      <h1 className="text-2xl font-black">دسترسی ندارید</h1>
      <p className="mt-3 leading-8 text-fg-muted">
        {wanted ? `اجازه ورود به بخش «${wanted}» برای حساب شما فعال نشده است.` : "هیچ بخشی برای حساب شما فعال نشده است."} برای دریافت دسترسی با مالک مجموعه صحبت کنید.
      </p>
      <button type="button" onClick={onGoHome} className={buttonClasses("dark", "md", "mt-6")}>
        بازگشت
      </button>
    </div>
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
            <PasswordInput
              id="admin-password"
              onDark
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
