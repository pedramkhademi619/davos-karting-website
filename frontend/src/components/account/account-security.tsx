"use client";

import { useCallback, useEffect, useState } from "react";
import { buttonClasses } from "@/components/button-link";
import { ShieldIcon } from "@/components/icons";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { ApiError, api, errorMessage } from "@/lib/api";
import { dateTime, deviceName, fa } from "@/lib/format";
import type { DeviceSession, Me } from "@/lib/types";

/** The devices signed in to the account; any other one can be signed out. */
export function AccountSecurity({ me, onSignedOut, onLogout }: { me: Me; onSignedOut: () => void; onLogout: () => void }) {
  const [devices, setDevices] = useState<DeviceSession[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setDevices(await api<DeviceSession[]>("/auth/sessions"));
    } catch (err) {
      if (err instanceof ApiError && err.isUnauthenticated) onSignedOut();
      else setError(errorMessage(err));
    }
  }, [onSignedOut]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- the first fetch of this tab
    void load();
  }, [load]);

  async function revoke(id: string) {
    setBusyId(id);
    setError(null);
    try {
      await api<void>(`/auth/sessions/${id}`, { method: "DELETE", csrf: me.csrf_token });
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  async function revokeOthers() {
    if (!devices) return;
    setBusyId("all");
    setError(null);
    try {
      for (const device of devices.filter((d) => !d.is_current)) {
        await api<void>(`/auth/sessions/${device.session_id}`, { method: "DELETE", csrf: me.csrf_token });
      }
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  const others = devices?.filter((d) => !d.is_current) ?? [];

  return (
    <div className="space-y-6">
      <div className="panel flex items-start gap-4 p-6">
        <ShieldIcon className="mt-1 h-7 w-7 shrink-0 text-gold" />
        <p className="leading-8 text-fg-muted">
          ورود به حساب فقط با کد پیامکی انجام می‌شود و رمز عبوری ذخیره نمی‌شود. اگر دستگاهی را نمی‌شناسید یا گوشی خود را گم کرده‌اید، آن را از اینجا
          خارج کنید.
        </p>
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      {!devices && !error ? (
        <div className="grid min-h-[12vh] place-items-center">
          <Spinner className="h-7 w-7" />
        </div>
      ) : (
        devices && (
          <ul className="divide-y divide-line rounded-3xl border border-line bg-surface">
            {devices.map((d) => (
              <li key={d.session_id} className="flex flex-wrap items-center justify-between gap-4 px-5 py-4">
                <div>
                  <p className="font-black">
                    {deviceName(d.user_agent)}
                    {d.is_current && (
                      <span className="mr-2 rounded-full bg-go-soft px-2.5 py-0.5 text-xs font-bold text-[#064d29]">این دستگاه</span>
                    )}
                  </p>
                  <p className="mt-1 text-sm text-fg-muted">
                    آخرین فعالیت: {dateTime(d.last_seen_at)}
                    {d.ip_hint && <span dir="ltr"> · IP {fa(d.ip_hint)}</span>}
                  </p>
                  <p className="text-xs text-fg-subtle">ورود: {dateTime(d.created_at)}</p>
                </div>
                {!d.is_current && (
                  <button
                    type="button"
                    disabled={busyId !== null}
                    onClick={() => revoke(d.session_id)}
                    className={buttonClasses("ghost", "sm")}
                  >
                    {busyId === d.session_id ? <Spinner /> : "خروج این دستگاه"}
                  </button>
                )}
              </li>
            ))}
          </ul>
        )
      )}

      <div className="flex flex-wrap gap-3">
        {others.length > 0 && (
          <button type="button" disabled={busyId !== null} onClick={revokeOthers} className={buttonClasses("signal", "md")}>
            {busyId === "all" ? <Spinner /> : `خروج از ${fa(others.length)} دستگاه دیگر`}
          </button>
        )}
        <button type="button" onClick={onLogout} className={buttonClasses("ghost", "md")}>
          خروج از این دستگاه
        </button>
      </div>
    </div>
  );
}
