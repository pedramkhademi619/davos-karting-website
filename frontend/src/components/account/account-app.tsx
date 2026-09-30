"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { OtpLogin } from "@/components/auth/otp-login";
import { useCountdown } from "@/components/booking/use-countdown";
import { buttonClasses } from "@/components/button-link";
import { LogoutIcon, TicketIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/ui/status-badge";
import { site } from "@/content/site";
import { ApiError, api, errorMessage } from "@/lib/api";
import { fa, jalali, karts, mobile, toman } from "@/lib/format";
import { goToGateway } from "@/lib/gateway";
import type { Me, Profile, Reservation, StartPayment } from "@/lib/types";
import { useCustomer } from "@/lib/use-customer";

/** The customer's tickets (pay a held one, see codes) and profile (name, SMS news consent), plus sign-out. */
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
  const [profile, setProfile] = useState<Profile | null>(null);
  const [tickets, setTickets] = useState<Reservation[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [p, r] = await Promise.all([api<Profile>("/account/profile"), api<Reservation[]>("/account/reservations")]);
      setProfile(p);
      setTickets(r);
    } catch (err) {
      if (err instanceof ApiError && err.isUnauthenticated) onSignedOut();
      else setError(errorMessage(err));
    }
  }, [onSignedOut]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api<Profile>("/account/profile"), api<Reservation[]>("/account/reservations")])
      .then(([p, r]) => {
        if (cancelled) return;
        setProfile(p);
        setTickets(r);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.isUnauthenticated) onSignedOut();
        else setError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [onSignedOut]);

  async function logout() {
    try {
      await api<void>("/auth/logout", { method: "POST", csrf: me.csrf_token });
    } finally {
      onSignedOut();
    }
  }

  if (error) return <Alert tone="error">{error}</Alert>;
  if (!profile || !tickets) {
    return (
      <div className="grid min-h-[30vh] place-items-center">
        <Spinner className="h-9 w-9" />
      </div>
    );
  }

  const upcoming = tickets.filter((t) => t.status === "held" || t.status === "confirmed");
  const past = tickets.filter((t) => t.status !== "held" && t.status !== "confirmed");

  return (
    <div className="grid gap-8 lg:grid-cols-12">
      <div className="space-y-8 lg:col-span-8">
        <section>
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-2xl font-black">بلیت‌های پیش رو</h2>
            <Link href={site.booking.href} className={buttonClasses("primary", "sm")}>
              رزرو جدید
            </Link>
          </div>
          {upcoming.length === 0 ? (
            <div className="panel-soft mt-5 p-8 text-center">
              <TicketIcon className="mx-auto h-10 w-10 text-fg-subtle" />
              <p className="mt-4 font-bold">هنوز بلیتی ندارید.</p>
              <p className="mt-2 text-fg-muted">سانس دلخواه را انتخاب کنید و پشت فرمان بنشینید.</p>
            </div>
          ) : (
            <ul className="mt-5 space-y-4">
              {upcoming.map((ticket) => (
                <TicketCard key={ticket.id} ticket={ticket} me={me} onChanged={load} />
              ))}
            </ul>
          )}
        </section>

        {past.length > 0 && (
          <section>
            <h2 className="text-xl font-black">سابقه</h2>
            <ul className="mt-4 divide-y divide-line rounded-3xl border border-line bg-surface">
              {past.map((ticket) => (
                <li key={ticket.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                  <span className="font-bold">
                    {ticket.weekday} {jalali(ticket.date_jalali)}، {fa(ticket.time)}
                  </span>
                  <span className="text-sm text-fg-muted">{karts(ticket.single_count, ticket.double_count)}</span>
                  <StatusBadge status={ticket.status} />
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <aside className="space-y-5 lg:col-span-4">
        <ProfileCard profile={profile} me={me} onSaved={setProfile} />
        <button type="button" onClick={logout} className={buttonClasses("ghost", "md", "w-full")}>
          <LogoutIcon className="h-5 w-5" />
          خروج از حساب
        </button>
      </aside>
    </div>
  );
}

function TicketCard({ ticket, me, onChanged }: { ticket: Reservation; me: Me; onChanged: () => void }) {
  const left = useCountdown(ticket.status === "held" ? ticket.hold_expires_at : null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const held = ticket.status === "held";
  const expired = held && left !== null && left <= 0;

  async function pay() {
    setBusy(true);
    setError(null);
    try {
      const start = await api<StartPayment>(`/reservations/${ticket.id}/pay`, { method: "POST", csrf: me.csrf_token });
      goToGateway(start);
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  async function release() {
    setBusy(true);
    setError(null);
    try {
      await api<void>(`/reservations/${ticket.id}`, { method: "DELETE", csrf: me.csrf_token });
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className="carbon overflow-hidden rounded-[1.75rem]">
      <div className="flex flex-wrap items-start justify-between gap-5 p-6">
        <div>
          <StatusBadge status={ticket.status} />
          <p className="mt-3 text-2xl font-black">
            {ticket.weekday} {jalali(ticket.date_jalali)}، ساعت {fa(ticket.time)}
          </p>
          <p className="mt-1 text-on-carbon-muted">
            {karts(ticket.single_count, ticket.double_count)} · {toman(ticket.amount_toman)}
          </p>
        </div>
        <div className="text-left">
          <p className="text-xs text-on-carbon-muted">کد رزرو</p>
          <p className="race-number mt-1 text-2xl font-black tracking-wider text-accent" dir="ltr">
            {ticket.code}
          </p>
        </div>
      </div>
      {held && (
        <div className="space-y-3 border-t border-carbon-line p-6">
          {error && <Alert tone="error">{error}</Alert>}
          {expired ? (
            <p className="text-sm text-on-carbon-muted">زمان پرداخت این رزرو تمام شده است.</p>
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              <button type="button" onClick={pay} disabled={busy} className={buttonClasses("primary", "md")}>
                {busy ? <Spinner /> : `پرداخت ${toman(ticket.amount_toman)}`}
              </button>
              <button type="button" onClick={release} disabled={busy} className={buttonClasses("ghost-light", "md")}>
                انصراف
              </button>
              {left !== null && (
                <span className="text-sm text-on-carbon-muted">
                  {fa(Math.floor(left / 60))} دقیقه و {fa(left % 60)} ثانیه تا پایان نگه‌داری
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </li>
  );
}

function ProfileCard({ profile, me, onSaved }: { profile: Profile; me: Me; onSaved: (p: Profile) => void }) {
  const [name, setName] = useState(profile.full_name);
  const [news, setNews] = useState(profile.marketing_opt_in);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      const saved = await api<Profile>("/account/profile", {
        method: "PUT",
        csrf: me.csrf_token,
        body: { full_name: name.trim(), marketing_opt_in: news },
      });
      onSaved(saved);
      setMessage({ tone: "success", text: "ذخیره شد." });
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} className="panel space-y-5 p-6">
      <div>
        <p className="text-sm text-fg-muted">شماره موبایل</p>
        <p className="mt-1 text-lg font-black" dir="ltr">
          {mobile(profile.mobile)}
        </p>
      </div>
      <div>
        <label htmlFor="profile-name" className="label">
          نام و نام خانوادگی
        </label>
        <input id="profile-name" className="field" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} autoComplete="name" />
      </div>
      <label className="flex cursor-pointer items-start gap-3">
        <input type="checkbox" checked={news} onChange={(e) => setNews(e.target.checked)} className="mt-1.5 h-5 w-5 accent-[#0c0d10]" />
        <span className="text-sm leading-7 text-fg-muted">پیامک خبرها و پیشنهادهای داوس را دریافت می‌کنم (هر زمان قابل لغو).</span>
      </label>
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      <button type="submit" disabled={busy} className={buttonClasses("dark", "md", "w-full")}>
        {busy ? <Spinner /> : "ذخیره"}
      </button>
    </form>
  );
}
