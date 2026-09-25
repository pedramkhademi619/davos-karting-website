"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { buttonClasses } from "@/components/button-link";
import { CheckIcon, CloseIcon } from "@/components/icons";
import { StartLights } from "@/components/start-lights";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { site } from "@/content/site";
import { ApiError, api } from "@/lib/api";
import { fa, jalali, karts, toman } from "@/lib/format";
import type { PaymentStatus, Reservation } from "@/lib/types";
import { SPLIT_HOSTS, hrefFor } from "@/lib/urls";

const HOME = hrefFor("/", SPLIT_HOSTS); // the main site, also from the booking subdomain

const POLL_MS = 2000;
const POLL_LIMIT = 20; // about 40 seconds; after that the reconciliation job keeps checking with the bank

type View =
  | { kind: "checking" }
  | { kind: "paid"; payment: PaymentStatus; reservation: Reservation | null }
  | { kind: "pending"; payment: PaymentStatus }
  | { kind: "refund"; payment: PaymentStatus }
  | { kind: "failed" }
  | { kind: "signed-out" }
  | { kind: "error"; message: string };

/**
 * Where the bank sends the customer back (via the API's callback). The page never trusts the query string: it asks the API
 * for the payment's verified status, and waits while the API is still verifying with the bank.
 */
export function PaymentResult() {
  const params = useSearchParams();
  const paymentId = params.get("payment");
  const failedAtBank = params.get("error") !== null;
  const [view, setView] = useState<View>(() => (paymentId && !failedAtBank ? { kind: "checking" } : { kind: "failed" }));

  useEffect(() => {
    if (!paymentId || failedAtBank) return;
    let cancelled = false;
    let attempts = 0;
    let timer: number | undefined;

    async function check() {
      attempts += 1;
      try {
        const payment = await api<PaymentStatus>(`/payments/${encodeURIComponent(paymentId as string)}`);
        if (cancelled) return;
        if (payment.status === "paid") {
          const reservation = payment.reservation_id
            ? await api<Reservation>(`/account/reservations/${payment.reservation_id}`).catch(() => null)
            : null;
          if (!cancelled) setView({ kind: "paid", payment, reservation });
          return;
        }
        if (payment.status === "refund_pending" || payment.status === "reversed") {
          setView({ kind: "refund", payment });
          return;
        }
        if (payment.status === "failed" || payment.status === "expired") {
          setView({ kind: "failed" });
          return;
        }
        // created / redirected / verifying / unknown: the API is still settling it with the bank.
        if (attempts >= POLL_LIMIT) {
          setView({ kind: "pending", payment });
          return;
        }
        timer = window.setTimeout(check, POLL_MS);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.isUnauthenticated) setView({ kind: "signed-out" });
        else setView({ kind: "error", message: err instanceof ApiError ? err.message : "وضعیت پرداخت دریافت نشد." });
      }
    }

    void check();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [paymentId, failedAtBank]);

  if (view.kind === "checking") {
    return (
      <Panel>
        <div className="flex flex-col items-center gap-6 py-10 text-center">
          <StartLights />
          <p className="text-2xl font-black">در حال تایید پرداخت با بانک...</p>
          <p className="text-on-carbon-muted">چند ثانیه صبر کنید؛ این صفحه را نبندید.</p>
          <Spinner className="h-7 w-7 text-accent" />
        </div>
      </Panel>
    );
  }

  if (view.kind === "paid") {
    const r = view.reservation;
    return (
      <Panel>
        <div className="text-center">
          <span className="pop mx-auto grid h-20 w-20 place-items-center rounded-full bg-go text-white shadow-[0_0_40px_rgb(30_224_122/0.5)]">
            <CheckIcon className="h-10 w-10" />
          </span>
          <h1 className="mt-6 text-3xl font-black md:text-4xl">رزرو شما قطعی شد!</h1>
          <p className="mt-3 text-on-carbon-muted">کد رزرو برایتان پیامک می‌شود. همین کد را در پیست نشان دهید.</p>
        </div>
        {r && (
          <div className="ticket mt-8 bg-white/[0.06] p-6 ring-1 ring-white/10">
            <p className="text-center text-sm text-on-carbon-muted">کد رزرو</p>
            <p className="race-number mt-2 text-center text-4xl font-black tracking-wider text-accent" dir="ltr">
              {r.code}
            </p>
            <dl className="mt-6 grid grid-cols-2 gap-4 text-center">
              <Fact label="روز" value={`${r.weekday} ${jalali(r.date_jalali)}`} />
              <Fact label="ساعت" value={fa(r.time)} />
              <Fact label="خودروها" value={karts(r.single_count, r.double_count)} />
              <Fact label="مبلغ" value={toman(r.amount_toman)} />
            </dl>
          </div>
        )}
        {view.payment.reference_id && (
          <p className="mt-6 text-center text-sm text-on-carbon-muted">
            کد پیگیری بانک: <span dir="ltr">{fa(view.payment.reference_id)}</span>
          </p>
        )}
        <Actions primary={{ href: "/account", label: "بلیت‌های من" }} secondary={{ href: HOME, label: "صفحه اصلی" }} />
      </Panel>
    );
  }

  if (view.kind === "refund") {
    return (
      <Panel>
        <h1 className="text-2xl font-black md:text-3xl">پرداخت انجام شد ولی رزرو ثبت نشد</h1>
        <p className="mt-4 text-on-carbon-muted">
          متأسفیم؛ جای این سانس در همین فاصله پر شد یا زمان نگه‌داری آن تمام شده بود. مبلغ{" "}
          {view.payment.amount_toman ? toman(view.payment.amount_toman) : ""} به‌طور خودکار به حساب شما برمی‌گردد
          {view.payment.status === "reversed" ? " (برگشت انجام شده است)" : ""}.
        </p>
        <Actions primary={{ href: site.booking.href, label: "انتخاب سانس دیگر" }} secondary={{ href: "/account", label: "حساب من" }} />
      </Panel>
    );
  }

  if (view.kind === "pending") {
    return (
      <Panel>
        <h1 className="text-2xl font-black md:text-3xl">پاسخ بانک هنوز قطعی نیست</h1>
        <p className="mt-4 text-on-carbon-muted">
          پرداخت شما در حال پیگیری خودکار با بانک است. تا چند دقیقه دیگر وضعیت در «حساب من» معلوم می‌شود. اگر مبلغ کم شده ولی رزرو قطعی
          نشد، بانک آن را برمی‌گرداند.
        </p>
        <Actions primary={{ href: "/account", label: "حساب من" }} secondary={{ href: site.contact.phone.href, label: "تماس با پشتیبانی" }} />
      </Panel>
    );
  }

  if (view.kind === "signed-out") {
    return (
      <Panel>
        <h1 className="text-2xl font-black">برای دیدن نتیجه وارد شوید</h1>
        <p className="mt-4 text-on-carbon-muted">نتیجه پرداخت فقط به صاحب حساب نشان داده می‌شود.</p>
        <Actions primary={{ href: "/login?next=/account", label: "ورود" }} secondary={{ href: HOME, label: "صفحه اصلی" }} />
      </Panel>
    );
  }

  if (view.kind === "error") {
    return (
      <Panel>
        <Alert tone="error">{view.message}</Alert>
        <Actions primary={{ href: "/account", label: "حساب من" }} secondary={{ href: HOME, label: "صفحه اصلی" }} />
      </Panel>
    );
  }

  return (
    <Panel>
      <div className="text-center">
        <span className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-signal text-white">
          <CloseIcon className="h-10 w-10" />
        </span>
        <h1 className="mt-6 text-3xl font-black">پرداخت انجام نشد</h1>
        <p className="mt-3 text-on-carbon-muted">
          اگر مبلغی از حسابتان کم شده باشد، طبق قوانین شاپرک حداکثر تا ۷۲ ساعت به حسابتان برمی‌گردد. خودروها تا پایان زمان نگه‌داری هنوز
          مال شماست و می‌توانید دوباره پرداخت کنید.
        </p>
      </div>
      <Actions primary={{ href: "/account", label: "پرداخت دوباره" }} secondary={{ href: site.booking.href, label: "انتخاب سانس" }} />
    </Panel>
  );
}

function Panel({ children }: { children: React.ReactNode }) {
  return <div className="carbon mx-auto max-w-2xl overflow-hidden rounded-[2rem] p-7 shadow-[0_40px_80px_-40px_rgb(12_13_16/0.9)] md:p-10">{children}</div>;
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-on-carbon-muted">{label}</dt>
      <dd className="mt-1 font-black">{value}</dd>
    </div>
  );
}

function Actions({ primary, secondary }: { primary: { href: string; label: string }; secondary: { href: string; label: string } }) {
  const link = (href: string, label: string, classes: string) =>
    href.startsWith("/") ? (
      <Link href={href} className={classes}>
        {label}
      </Link>
    ) : (
      <a href={href} className={classes}>
        {label}
      </a>
    );
  return (
    <div className="mt-8 flex flex-wrap justify-center gap-3">
      {link(primary.href, primary.label, buttonClasses("primary", "md"))}
      {link(secondary.href, secondary.label, buttonClasses("ghost-light", "md"))}
    </div>
  );
}
