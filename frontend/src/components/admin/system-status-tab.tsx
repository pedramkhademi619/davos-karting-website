"use client";

import { useCallback, useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, TabHeader } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { RefreshIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { clock, fa } from "@/lib/format";
import type { ServiceStatus, StatusLevel, SystemStatus } from "@/lib/types";

const LEVEL: Record<StatusLevel, { label: string; badge: string; dot: string }> = {
  ok: { label: "سالم", badge: "bg-go-soft text-[#064d29] ring-go/25", dot: "bg-go" },
  degraded: { label: "نیازمند توجه", badge: "bg-[#fff3c4] text-ink-soft ring-accent/60", dot: "bg-accent" },
  down: { label: "از کار افتاده", badge: "bg-signal-soft text-[#7a0600] ring-signal/25", dot: "bg-signal" },
  disabled: { label: "غیرفعال", badge: "bg-surface-2 text-fg-muted ring-line-strong", dot: "bg-fg-subtle" },
  test: { label: "آزمایشی", badge: "bg-[#e3ecff] text-[#1b3a8a] ring-[#1b3a8a]/20", dot: "bg-[#3b6cf6]" },
};

const OVERALL: Record<"ok" | "degraded" | "down", { text: string; tone: "success" | "warning" | "error" }> = {
  ok: { text: "همه سرویس‌ها سالم‌اند.", tone: "success" },
  degraded: { text: "همه‌چیز کار می‌کند ولی بعضی موارد نیاز به توجه دارند.", tone: "warning" },
  down: { text: "حداقل یک سرویس از کار افتاده است.", tone: "error" },
};

const GROUPS = ["زیرساخت", "سرویس‌های بیرونی", "برنامه"];
const REFRESH_MS = 15_000;

function Badge({ level }: { level: StatusLevel }) {
  const style = LEVEL[level];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ring-1 ${style.badge}`}>
      <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {style.label}
    </span>
  );
}

/** Live health of everything the site depends on: database, Redis, background jobs, SMS, bank gateway, AI, site and game. */
export function SystemStatusTab() {
  const { call } = useAdmin();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    try {
      setStatus(await call<SystemStatus>("/system/status"));
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }, [call]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- the first fetch of this tab
    void load();
    const timer = window.setInterval(() => {
      if (!document.hidden) void load();
    }, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  return (
    <div>
      <TabHeader
        title="وضعیت سرویس‌ها"
        lead="سلامت هر چیزی که سایت به آن وابسته است. این صفحه هر ۱۵ ثانیه خودش به‌روز می‌شود. برای اینکه به پیامک، درگاه بانک و هوش مصنوعی فشار نیاید، نتیجهٔ این سه حداکثر دقیقه‌ای یک‌بار تازه می‌شود."
        actions={
          <button type="button" onClick={load} disabled={busy} className={buttonClasses("dark", "sm")}>
            {busy ? <Spinner /> : <RefreshIcon className="h-4 w-4" />}
            بررسی دوباره
          </button>
        }
      />
      {error && (
        <Alert tone="error" className="mb-6">
          {error}
        </Alert>
      )}
      {!status ? (
        !error && <Spinner className="h-8 w-8" />
      ) : (
        <div className="space-y-8">
          <Alert tone={OVERALL[status.overall as "ok" | "degraded" | "down"].tone}>
            <span className="font-black">{OVERALL[status.overall as "ok" | "degraded" | "down"].text}</span> آخرین بررسی: {clock(status.checked_at)}
          </Alert>
          {GROUPS.map((group) => {
            const items = status.services.filter((s) => s.group === group);
            if (items.length === 0) return null;
            return (
              <section key={group} aria-label={group}>
                <h2 className="mb-4 text-xl font-black">{group}</h2>
                <div className="grid gap-5 xl:grid-cols-2">
                  {items.map((service) => (
                    <ServiceCard key={service.key} service={service} />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ServiceCard({ service }: { service: ServiceStatus }) {
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="text-lg font-black">{service.label}</h3>
        <Badge level={service.level} />
      </div>
      <p className="mt-2 text-sm leading-7 text-fg-muted">{service.summary}</p>
      {service.latency_ms !== null && <p className="mt-1 text-xs text-fg-subtle">زمان پاسخ: {fa(service.latency_ms)} میلی‌ثانیه</p>}
      {service.parts.length > 0 && (
        <ul className="mt-4 divide-y divide-line rounded-2xl border border-line">
          {service.parts.map((part) => (
            <li key={part.label} className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 text-sm">
              <span className="flex items-center gap-2 font-bold">
                <span aria-hidden="true" className={`h-2 w-2 rounded-full ${LEVEL[part.level].dot}`} />
                {part.label}
              </span>
              <span className="text-fg-muted" dir="auto">
                {part.detail}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
