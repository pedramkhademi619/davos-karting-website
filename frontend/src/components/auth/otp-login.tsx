"use client";

import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { api, errorMessage } from "@/lib/api";
import { fa, mobile as formatMobile, toLatinDigits } from "@/lib/format";
import type { Me, OtpRequested, SignedIn } from "@/lib/types";

/** "۰۹۱۲..." / "+98912..." / "912..." -> "0912...", or null when it is not an Iranian mobile number. */
export function normaliseMobile(raw: string): string | null {
  let digits = toLatinDigits(raw).replace(/\D/g, "");
  if (digits.startsWith("0098")) digits = digits.slice(4);
  else if (digits.startsWith("98") && digits.length === 12) digits = digits.slice(2);
  if (digits.length === 10 && digits.startsWith("9")) digits = `0${digits}`;
  return /^09\d{9}$/.test(digits) ? digits : null;
}

type OtpLoginProps = {
  onSignedIn: (me: Me) => void;
  tone?: "light" | "dark";
  title?: string;
};

/** Sign-in with a one-time SMS code (Kavenegar). No passwords; the session cookie is set by the API. */
export function OtpLogin({ onSignedIn, tone = "light", title = "ورود با شماره موبایل" }: OtpLoginProps) {
  const [step, setStep] = useState<"mobile" | "code">("mobile");
  const [mobileInput, setMobileInput] = useState("");
  const [mobile, setMobile] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resendAt, setResendAt] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const codeRef = useRef<HTMLInputElement>(null);
  const mobileId = useId();
  const codeId = useId();
  const dark = tone === "dark";

  useEffect(() => {
    if (step !== "code") return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    codeRef.current?.focus();
    return () => window.clearInterval(timer);
  }, [step]);

  const resendIn = Math.max(0, Math.ceil((resendAt - now) / 1000));

  async function requestCode(target: string) {
    setBusy(true);
    setError(null);
    try {
      const sent = await api<OtpRequested>("/auth/otp/request", { method: "POST", body: { mobile: target } });
      setMobile(target);
      setStep("code");
      setCode("");
      setResendAt(Date.now() + sent.resend_after_seconds * 1000);
      setNow(Date.now());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function onMobile(event: FormEvent) {
    event.preventDefault();
    const normalised = normaliseMobile(mobileInput);
    if (!normalised) {
      setError("شماره موبایل را درست وارد کنید؛ مثل ۰۹۱۲۳۴۵۶۷۸۹.");
      return;
    }
    await requestCode(normalised);
  }

  async function onCode(event: FormEvent) {
    event.preventDefault();
    const clean = toLatinDigits(code).replace(/\D/g, "");
    if (clean.length < 4) {
      setError("کد پیامک‌شده را کامل وارد کنید.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const session = await api<SignedIn>("/auth/otp/verify", { method: "POST", body: { mobile, code: clean } });
      onSignedIn({ user_id: session.user_id, csrf_token: session.csrf_token });
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  const field = `field text-center text-lg font-bold tracking-widest ${dark ? "field-dark" : ""}`;

  return (
    <div>
      <h3 className="text-xl font-black">{title}</h3>
      {step === "mobile" ? (
        <form onSubmit={onMobile} className="mt-5 space-y-4" noValidate>
          <p className={dark ? "text-on-carbon-muted" : "text-fg-muted"}>کد ورود برایتان پیامک می‌شود؛ رمز عبور لازم نیست.</p>
          <div>
            <label htmlFor={mobileId} className="label">
              شماره موبایل
            </label>
            <input
              id={mobileId}
              dir="ltr"
              inputMode="tel"
              autoComplete="tel"
              placeholder="09xx xxx xxxx"
              className={field}
              value={mobileInput}
              onChange={(event) => setMobileInput(event.target.value)}
              aria-invalid={error ? true : undefined}
              maxLength={16}
            />
          </div>
          {error && <Alert tone="error">{error}</Alert>}
          <button type="submit" disabled={busy} className={buttonClasses("primary", "lg", "w-full")}>
            {busy ? <Spinner label="در حال ارسال کد" /> : "ارسال کد"}
          </button>
        </form>
      ) : (
        <form onSubmit={onCode} className="mt-5 space-y-4" noValidate>
          <p className={dark ? "text-on-carbon-muted" : "text-fg-muted"}>
            کد به <span dir="ltr" className="font-bold">{formatMobile(mobile)}</span> پیامک شد.{" "}
            <button type="button" className="font-bold underline underline-offset-4" onClick={() => setStep("mobile")}>
              تغییر شماره
            </button>
          </p>
          <div>
            <label htmlFor={codeId} className="label">
              کد تایید
            </label>
            <input
              id={codeId}
              ref={codeRef}
              dir="ltr"
              inputMode="numeric"
              autoComplete="one-time-code"
              className={field}
              value={code}
              onChange={(event) => setCode(event.target.value)}
              aria-invalid={error ? true : undefined}
              maxLength={8}
            />
          </div>
          {error && <Alert tone="error">{error}</Alert>}
          <button type="submit" disabled={busy} className={buttonClasses("primary", "lg", "w-full")}>
            {busy ? <Spinner label="در حال بررسی کد" /> : "ورود"}
          </button>
          <p className={`text-center text-sm ${dark ? "text-on-carbon-muted" : "text-fg-muted"}`}>
            {resendIn > 0 ? (
              <>ارسال دوباره تا {fa(resendIn)} ثانیه دیگر</>
            ) : (
              <button type="button" disabled={busy} className="font-bold underline underline-offset-4" onClick={() => requestCode(mobile)}>
                ارسال دوباره کد
              </button>
            )}
          </p>
        </form>
      )}
    </div>
  );
}
