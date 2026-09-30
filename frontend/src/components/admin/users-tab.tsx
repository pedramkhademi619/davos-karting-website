"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, TabHeader, Table, cell } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { dateTime } from "@/lib/format";
import type { AdminUser } from "@/lib/types";

/** Staff accounts (owner only) and changing one's own password (everyone). */
export function UsersTab() {
  const { call, isOwner, me } = useAdmin();
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (!isOwner) return;
    let cancelled = false;
    call<AdminUser[]>("/users")
      .then((result) => !cancelled && setUsers(result))
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, isOwner, version]);

  async function toggle(user: AdminUser) {
    try {
      await call(`/users/${user.admin_id}/active`, { method: "POST", body: { is_active: !user.is_active } });
      setVersion((v) => v + 1);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <div>
      <TabHeader title="کاربران پنل" lead="هر نفر حساب جدا داشته باشد تا کارهایش در سوابق با نام خودش ثبت شود." />
      {error && (
        <Alert tone="error" className="mb-6">
          {error}
        </Alert>
      )}
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="space-y-6 xl:col-span-8">
          {isOwner ? (
            <Card title="حساب‌ها">
              {!users ? (
                <Spinner className="h-7 w-7" />
              ) : (
                <Table head={["نام کاربری", "نام", "نقش", "آخرین ورود", "وضعیت", ""]} empty={users.length === 0}>
                  {users.map((u) => (
                    <tr key={u.admin_id}>
                      <td className={`${cell} font-bold`} dir="ltr">
                        {u.username}
                      </td>
                      <td className={cell}>{u.display_name || "—"}</td>
                      <td className={cell}>{u.role === "owner" ? "مالک" : "کارمند"}</td>
                      <td className={cell}>{u.last_login_at ? dateTime(u.last_login_at) : "—"}</td>
                      <td className={cell}>{u.is_active ? "فعال" : "غیرفعال"}</td>
                      <td className={cell}>
                        {u.admin_id !== me.admin_id && (
                          <button type="button" className="text-xs font-bold underline" onClick={() => toggle(u)}>
                            {u.is_active ? "غیرفعال کردن" : "فعال کردن"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </Table>
              )}
            </Card>
          ) : (
            <Alert tone="info">فقط مالک می‌تواند حساب‌های پنل را ببیند و بسازد.</Alert>
          )}
          {isOwner && <CreateUser onCreated={() => setVersion((v) => v + 1)} />}
        </div>
        <div className="xl:col-span-4">
          <ChangePassword />
        </div>
      </div>
    </div>
  );
}

function CreateUser({ onCreated }: { onCreated: () => void }) {
  const { call } = useAdmin();
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"staff" | "owner">("staff");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      await call("/users", { method: "POST", body: { username: username.trim(), display_name: displayName.trim(), password, role } });
      setMessage({ tone: "success", text: "حساب ساخته شد." });
      setUsername("");
      setDisplayName("");
      setPassword("");
      onCreated();
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="افزودن حساب">
      <form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
        <label className="block">
          <span className="label">نام کاربری (انگلیسی)</span>
          <input className="field" dir="ltr" value={username} onChange={(e) => setUsername(e.target.value)} minLength={3} maxLength={32} required autoComplete="off" />
        </label>
        <label className="block">
          <span className="label">نام نمایشی</span>
          <input className="field" value={displayName} onChange={(e) => setDisplayName(e.target.value)} maxLength={60} />
        </label>
        <label className="block">
          <span className="label">رمز عبور (حداقل ۱۲ نویسه)</span>
          <input className="field" type="password" dir="ltr" value={password} onChange={(e) => setPassword(e.target.value)} minLength={12} required autoComplete="new-password" />
        </label>
        <label className="block">
          <span className="label">نقش</span>
          <select className="field" value={role} onChange={(e) => setRole(e.target.value as "staff" | "owner")}>
            <option value="staff">کارمند (رزروها، مشتریان، پیامک)</option>
            <option value="owner">مالک (همه‌چیز، شامل قیمت‌ها و حساب‌ها)</option>
          </select>
        </label>
        {message && <Alert tone={message.tone} className="md:col-span-2">{message.text}</Alert>}
        <div className="md:col-span-2">
          <button type="submit" disabled={busy} className={buttonClasses("dark", "md")}>
            {busy ? <Spinner /> : "ساخت حساب"}
          </button>
        </div>
      </form>
    </Card>
  );
}

function ChangePassword() {
  const { call } = useAdmin();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [repeat, setRepeat] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (next !== repeat) {
      setMessage({ tone: "error", text: "رمز جدید و تکرار آن یکی نیستند." });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await call<void>("/auth/password", { method: "POST", body: { current_password: current, new_password: next } });
      setMessage({ tone: "success", text: "رمز عبور عوض شد." });
      setCurrent("");
      setNext("");
      setRepeat("");
    } catch (err) {
      setMessage({ tone: "error", text: errorMessage(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="تغییر رمز عبور من">
      <form onSubmit={submit} className="space-y-4">
        <input className="field" type="password" dir="ltr" placeholder="رمز فعلی" value={current} onChange={(e) => setCurrent(e.target.value)} required autoComplete="current-password" aria-label="رمز فعلی" />
        <input className="field" type="password" dir="ltr" placeholder="رمز جدید (حداقل ۱۲)" value={next} onChange={(e) => setNext(e.target.value)} minLength={12} required autoComplete="new-password" aria-label="رمز جدید" />
        <input className="field" type="password" dir="ltr" placeholder="تکرار رمز جدید" value={repeat} onChange={(e) => setRepeat(e.target.value)} minLength={12} required autoComplete="new-password" aria-label="تکرار رمز جدید" />
        {message && <Alert tone={message.tone}>{message.text}</Alert>}
        <button type="submit" disabled={busy} className={buttonClasses("dark", "md", "w-full")}>
          {busy ? <Spinner /> : "تغییر رمز"}
        </button>
      </form>
    </Card>
  );
}
