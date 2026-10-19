"use client";

import { useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Kpi, TabHeader } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { RefreshIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { errorMessage } from "@/lib/api";
import { fa, number, toman } from "@/lib/format";
import type { Dashboard } from "@/lib/types";
import { PageSkeleton } from "@/components/ui/skeleton";
import { greeting } from "@/lib/greeting";

type Target = "reservations" | "payments" | "sms" | "settings";

export function DashboardTab({ onOpen }: { onOpen: (tab: Target) => void }) {
  const { call, me } = useAdmin();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const first = me.display_name?.split(" ")[0] ?? "";

  useEffect(() => {
    let cancelled = false;
    call<Dashboard>("/dashboard")
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setError(null);
      })
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, version]);

  return (
    <div>
      <TabHeader
        title={`${greeting()}${first ? `، ${first}` : ""}`}
        lead={data ? todaySentence(data) : "دارم حال پیست را می‌گیرم…"}
        actions={
          <button type="button" onClick={() => setVersion((v) => v + 1)} className={buttonClasses("ghost", "sm")}>
            <RefreshIcon className="h-4 w-4" />
            به‌روزرسانی
          </button>
        }
      />
      {error && <Alert tone="error">{error}</Alert>}
      {!data && !error && <PageSkeleton variant="cards" />}
      {data && (
        <div className="space-y-6">
          {(!data.online_booking_enabled || !data.payments_enabled) && (
            <Alert tone="warning">
              {!data.online_booking_enabled && "رزرو آنلاین در تنظیمات خاموش است. "}
              {!data.payments_enabled && "پرداخت آنلاین (PAYMENTS_ENABLED) روی سرور فعال نیست؛ مشتری‌ها نمی‌توانند آنلاین بپردازند."}
            </Alert>
          )}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Kpi tone="dark" label="رزرو قطعی امروز" value={fa(data.today_confirmed)} note={`${fa(data.today_attended)} نفر حاضر شدند`} />
            <Kpi label="خودروهای امروز" value={fa(data.today_karts)} note={`${fa(data.today_people)} نفر`} />
            <Kpi label="رزرو قطعی فردا" value={fa(data.tomorrow_confirmed)} note={`${fa(data.tomorrow_karts)} خودرو`} />
            <Kpi tone="accent" label="در انتظار پرداخت" value={fa(data.held_now)} note="نگه‌داشته‌شده همین حالا" />
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <Kpi label="فروش آنلاین این ماه" value={<span className="text-2xl">{toman(data.month_online_revenue_toman)}</span>} />
            <Kpi label="رزروهای این ماه" value={number(data.month_reservations)} />
            <Kpi
              label="اعتبار پنل پیامک"
              value={<span className="text-2xl">{data.sms_credit_toman === null ? "—" : toman(data.sms_credit_toman)}</span>}
              note={data.sms_credit_toman === null ? "اتصال به کاوه‌نگار برقرار نیست یا تنظیم نشده" : undefined}
            />
          </div>
          <div className="flex flex-wrap gap-3">
            <button type="button" className={buttonClasses("dark", "md")} onClick={() => onOpen("reservations")}>
              سانس‌های امروز
            </button>
            <button type="button" className={buttonClasses("ghost", "md")} onClick={() => onOpen("sms")}>
              ارسال پیامک
            </button>
            <button type="button" className={buttonClasses("ghost", "md")} onClick={() => onOpen("settings")}>
              قیمت‌ها و ظرفیت
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/** One warm sentence about today and tomorrow, instead of a label that says what the page is. */
function todaySentence(d: Dashboard): string {
  const today =
    d.today_confirmed === 0
      ? "امروز هنوز رزروی نداریم؛ روزی آرام است."
      : `امروز ${fa(d.today_confirmed)} رزرو داریم، ${fa(d.today_karts)} خودرو و ${fa(d.today_people)} نفر` +
        (d.today_attended > 0 ? `؛ ${fa(d.today_attended)} نفرشان همین حالا آمده‌اند.` : ".");
  const tomorrow = d.tomorrow_confirmed > 0 ? ` فردا هم ${fa(d.tomorrow_confirmed)} رزرو در انتظارمان است.` : "";
  const held = d.held_now > 0 ? ` ${fa(d.held_now)} نفر هم الان دارند پرداخت می‌کنند.` : "";
  return today + tomorrow + held;
}
