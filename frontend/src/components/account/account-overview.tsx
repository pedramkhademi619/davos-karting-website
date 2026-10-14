"use client";

import Link from "next/link";
import { useMemo } from "react";
import { buttonClasses } from "@/components/button-link";
import { CalendarIcon, KartIcon, PinIcon, TicketIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { site } from "@/content/site";
import { dateOnly, dateTime, fa, jalali, karts, number, timeUntil, toman } from "@/lib/format";
import { downloadCalendarEvent } from "@/lib/ticket-tools";
import type { AccountPayment, Profile, Reservation } from "@/lib/types";
import { accountStats, isOpenTicket } from "./use-account-data";
import { useNow } from "./use-now";

type Activity = { at: string; text: string };

function activity(tickets: Reservation[], payments: AccountPayment[]): Activity[] {
  const items: Activity[] = [];
  for (const t of tickets) {
    items.push({ at: t.created_at, text: `رزرو بلیت ${fa(t.ticket_number)} ثبت شد` });
    if (t.confirmed_at) items.push({ at: t.confirmed_at, text: `بلیت ${fa(t.ticket_number)} قطعی شد` });
    if (t.status === "attended") items.push({ at: t.starts_at, text: `حضور در سانس ${jalali(t.date_jalali)}، ${fa(t.time)}` });
  }
  for (const p of payments) {
    if (p.status === "paid") items.push({ at: p.updated_at, text: `پرداخت ${toman(p.amount_toman)} موفق بود` });
    else if (p.status === "failed") items.push({ at: p.updated_at, text: `پرداخت ${toman(p.amount_toman)} ناموفق بود` });
  }
  return items.sort((a, b) => b.at.localeCompare(a.at)).slice(0, 6);
}

/** The first tab: what is next, what is waiting for payment, totals, and recent activity. */
export function AccountOverview({
  profile,
  tickets,
  payments,
  goTo,
}: {
  profile: Profile;
  tickets: Reservation[];
  payments: AccountPayment[];
  goTo: (tab: "tickets" | "payments" | "profile") => void;
}) {
  const now = useNow();
  const stats = useMemo(() => accountStats(tickets, payments), [tickets, payments]);
  const next = useMemo(
    () =>
      tickets
        .filter((t) => t.status === "confirmed" && new Date(t.starts_at).getTime() > now - 30 * 60_000)
        .sort((a, b) => a.starts_at.localeCompare(b.starts_at))[0],
    [tickets, now],
  );
  const awaiting = tickets.filter((t) => t.status === "held" && t.hold_expires_at && new Date(t.hold_expires_at).getTime() > now);
  const recent = useMemo(() => activity(tickets, payments), [tickets, payments]);
  const open = tickets.filter(isOpenTicket).length;

  return (
    <div className="space-y-8">
      {awaiting.length > 0 && (
        <Alert tone="warning">
          <span className="font-black">{fa(awaiting.length)} رزرو منتظر پرداخت است.</span> مهلت پرداخت محدود است؛ برای نگه داشتن جا، پرداخت را کامل کنید.{" "}
          <button type="button" onClick={() => goTo("tickets")} className="font-black underline underline-offset-4">
            رفتن به بلیت‌ها
          </button>
        </Alert>
      )}

      {!profile.full_name.trim() && (
        <Alert tone="info">
          نام شما هنوز ثبت نشده است.{" "}
          <button type="button" onClick={() => goTo("profile")} className="font-black underline underline-offset-4">
            تکمیل پروفایل
          </button>
        </Alert>
      )}

      <section aria-label="سانس بعدی">
        {next ? (
          <div className="carbon overflow-hidden rounded-[1.75rem]">
            <div className="flex flex-wrap items-start justify-between gap-6 p-6 md:p-8">
              <div>
                <p className="text-sm font-bold text-accent">سانس بعدی شما</p>
                <p className="mt-3 text-3xl font-black">
                  {next.weekday} {jalali(next.date_jalali)}
                </p>
                <p className="mt-1 text-xl text-on-carbon-muted">
                  ساعت {fa(next.time)} · {karts(next.single_count, next.double_count)}
                </p>
                <p className="mt-4 inline-block rounded-full bg-white/10 px-4 py-1.5 text-sm font-bold">
                  {timeUntil(next.starts_at, now) ? `${timeUntil(next.starts_at, now)} دیگر` : "الان نوبت شماست"}
                </p>
              </div>
              <div className="text-left">
                <p className="text-xs text-on-carbon-muted">شماره بلیت</p>
                <p className="race-number mt-1 text-5xl font-black tracking-wider text-accent" dir="ltr">
                  {fa(next.ticket_number)}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3 border-t border-carbon-line p-5">
              <button type="button" onClick={() => downloadCalendarEvent(next)} className={buttonClasses("ghost-light", "sm")}>
                <CalendarIcon className="h-4 w-4" />
                افزودن به تقویم
              </button>
              <a href={site.contact.map.href} target="_blank" rel="noopener noreferrer" className={buttonClasses("ghost-light", "sm")}>
                <PinIcon className="h-4 w-4" />
                مسیریابی
              </a>
              <a href={site.contact.phone.href} className={buttonClasses("ghost-light", "sm")}>
                تماس با پیست
              </a>
            </div>
          </div>
        ) : (
          <div className="panel-soft p-8 text-center">
            <KartIcon className="mx-auto h-10 w-10 text-fg-subtle" />
            <p className="mt-4 text-lg font-black">سانس قطعی پیش رویی ندارید.</p>
            <p className="mt-2 text-fg-muted">سانس دلخواه را انتخاب کنید و پشت فرمان بنشینید.</p>
            <Link href={site.booking.href} className={buttonClasses("primary", "md", "mt-5")}>
              رزرو سانس
            </Link>
          </div>
        )}
      </section>

      <section aria-label="آمار" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="بلیت‌های فعال" value={fa(open)} onClick={() => goTo("tickets")} />
        <Stat label="دفعات حضور" value={fa(stats.visits)} hint={stats.karts ? `${fa(stats.karts)} خودرو رانده‌اید` : undefined} />
        <Stat label="مجموع پرداخت" value={number(stats.paidToman)} hint="تومان" onClick={() => goTo("payments")} />
        <Stat label="عضویت از" value={dateOnly(profile.created_at)} />
      </section>

      <section aria-label="فعالیت‌های اخیر">
        <h2 className="text-xl font-black">فعالیت‌های اخیر</h2>
        {recent.length === 0 ? (
          <p className="mt-4 text-fg-muted">هنوز فعالیتی ثبت نشده است.</p>
        ) : (
          <ol className="mt-4 divide-y divide-line rounded-3xl border border-line bg-surface">
            {recent.map((item, index) => (
              <li key={`${item.at}-${index}`} className="flex flex-wrap items-center justify-between gap-2 px-5 py-4">
                <span className="flex items-center gap-3 font-bold">
                  <TicketIcon className="h-5 w-5 text-fg-subtle" />
                  {item.text}
                </span>
                <span className="text-sm text-fg-muted">{dateTime(item.at)}</span>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value, hint, onClick }: { label: string; value: string; hint?: string; onClick?: () => void }) {
  const body = (
    <>
      <p className="text-sm text-fg-muted">{label}</p>
      <p className="mt-2 text-2xl font-black">{value}</p>
      {hint && <p className="mt-1 text-xs text-fg-subtle">{hint}</p>}
    </>
  );
  return onClick ? (
    <button type="button" onClick={onClick} className="panel p-5 text-right transition-shadow hover:shadow-lg">
      {body}
    </button>
  ) : (
    <div className="panel p-5">{body}</div>
  );
}
