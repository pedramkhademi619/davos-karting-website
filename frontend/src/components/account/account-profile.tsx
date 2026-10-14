"use client";

import { useState, type FormEvent } from "react";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { api, errorMessage } from "@/lib/api";
import { dateOnly, mobile } from "@/lib/format";
import type { Me, Profile } from "@/lib/types";

/** Name and SMS-news consent are editable; the mobile number is the sign-in identity and is shown read-only. */
export function AccountProfile({ profile, me, onSaved }: { profile: Profile; me: Me; onSaved: (p: Profile) => void }) {
  const [name, setName] = useState(profile.full_name);
  const [news, setNews] = useState(profile.marketing_opt_in);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const changed = name.trim() !== profile.full_name || news !== profile.marketing_opt_in;

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
    <form onSubmit={save} className="panel max-w-xl space-y-6 p-6 md:p-8">
      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <p className="text-sm text-fg-muted">شماره موبایل</p>
          <p className="mt-1 text-lg font-black" dir="ltr" style={{ textAlign: "right" }}>
            {mobile(profile.mobile)}
          </p>
          <p className="mt-1 text-xs leading-6 text-fg-subtle">شماره، هویت ورود شماست و از اینجا تغییر نمی‌کند.</p>
        </div>
        <div>
          <p className="text-sm text-fg-muted">عضویت از</p>
          <p className="mt-1 text-lg font-black">{dateOnly(profile.created_at)}</p>
        </div>
      </div>
      <div>
        <label htmlFor="profile-name" className="label">
          نام و نام خانوادگی
        </label>
        <input id="profile-name" className="field" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} autoComplete="name" />
        <p className="mt-2 text-xs leading-6 text-fg-subtle">این نام هنگام رزرو روی بلیت شما می‌آید.</p>
      </div>
      <label className="flex cursor-pointer items-start gap-3">
        <input type="checkbox" checked={news} onChange={(e) => setNews(e.target.checked)} className="mt-1.5 h-5 w-5 accent-[#0c0d10]" />
        <span className="text-sm leading-7 text-fg-muted">پیامک خبرها و پیشنهادهای داوس را دریافت می‌کنم (هر زمان قابل لغو). پیامک‌های تایید رزرو و کد ورود همیشه ارسال می‌شود.</span>
      </label>
      {message && <Alert tone={message.tone}>{message.text}</Alert>}
      <button type="submit" disabled={busy || !changed} className={buttonClasses("dark", "md", "w-full sm:w-auto")}>
        {busy ? <Spinner /> : "ذخیره تغییرات"}
      </button>
    </form>
  );
}
