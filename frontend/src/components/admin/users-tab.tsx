"use client";

import { PasswordInput } from "@/components/ui/password-input";
import { PermissionPicker } from "@/components/admin/permission-picker";
import { useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, TabHeader, Table, cell } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { dateTime } from "@/lib/format";
import type { AdminUser, PermissionCatalog } from "@/lib/types";

/** Staff accounts (owner only) and changing one's own password (everyone). */
export function UsersTab() {
  const { call, isOwner, me } = useAdmin();
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const [catalog, setCatalog] = useState<PermissionCatalog | null>(null);
  const [editing, setEditing] = useState<AdminUser | null>(null);

  useEffect(() => {
    if (!isOwner) return;
    let cancelled = false;
    call<PermissionCatalog>("/users/catalog")
      .then((result) => !cancelled && setCatalog(result))
      .catch((err) => !cancelled && setError(errorMessage(err)));
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
                <Table head={["نام کاربری", "نام", "نقش", "دسترسی‌ها", "آخرین ورود", "وضعیت", ""]} empty={users.length === 0}>
                  {users.map((u) => (
                    <tr key={u.admin_id}>
                      <td className={`${cell} font-bold`} dir="ltr">
                        {u.username}
                      </td>
                      <td className={cell}>{u.display_name || "—"}</td>
                      <td className={cell}>{u.role === "owner" ? "مالک" : "کارمند"}</td>
                      <td className={cell}>
                        {u.role === "owner" ? (
                          "همه بخش‌ها"
                        ) : (
                          <button type="button" className="font-bold underline underline-offset-4" onClick={() => setEditing(u)}>
                            {u.custom_permissions ? `${u.permissions.length.toLocaleString("fa-IR")} بخش` : "پیش‌فرض"} · تغییر
                          </button>
                        )}
                      </td>
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
          {isOwner && editing && catalog && (
            <EditPermissions
              key={editing.admin_id}
              user={editing}
              catalog={catalog}
              onClose={() => setEditing(null)}
              onSaved={() => {
                setEditing(null);
                setVersion((v) => v + 1);
              }}
            />
          )}
          {isOwner && catalog && <CreateUser catalog={catalog} onCreated={() => setVersion((v) => v + 1)} />}
        </div>
        <div className="xl:col-span-4">
          <ChangePassword />
        </div>
      </div>
    </div>
  );
}

function EditPermissions({ user, catalog, onClose, onSaved }: { user: AdminUser; catalog: PermissionCatalog; onClose: () => void; onSaved: () => void }) {
  const { call } = useAdmin();
  const [keys, setKeys] = useState<string[]>(user.permissions);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(permissions: string[] | null) {
    setBusy(true);
    setError(null);
    try {
      await call(`/users/${user.admin_id}/permissions`, { method: "PUT", body: { permissions } });
      onSaved();
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <Card title={`دسترسی‌های ${user.display_name || user.username}`}>
      <PermissionPicker catalog={catalog} value={keys} onChange={setKeys} />
      {error && (
        <Alert tone="error" className="mt-4">
          {error}
        </Alert>
      )}
      <div className="mt-5 flex flex-wrap gap-3">
        <button type="button" disabled={busy} onClick={() => save(keys)} className={buttonClasses("primary", "md")}>
          {busy ? <Spinner /> : "ذخیره دسترسی‌ها"}
        </button>
        <button type="button" disabled={busy} onClick={() => save(null)} className={buttonClasses("ghost", "md")}>
          بازگشت به پیش‌فرض
        </button>
        <button type="button" disabled={busy} onClick={onClose} className={buttonClasses("ghost", "md")}>
          انصراف
        </button>
      </div>
      <p className="mt-3 text-xs text-fg-subtle">تغییر از درخواست بعدی همان شخص اعمال می‌شود؛ لازم نیست دوباره وارد شود.</p>
    </Card>
  );
}

function CreateUser({ catalog, onCreated }: { catalog: PermissionCatalog; onCreated: () => void }) {
  const { call } = useAdmin();
  const [keys, setKeys] = useState<string[]>(() => catalog.entries.filter((entry) => entry.default_for_staff).map((entry) => entry.key));
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
      await call("/users", { method: "POST", body: { username: username.trim(), display_name: displayName.trim(), password, role, permissions: role === "staff" ? keys : null } });
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
          <PasswordInput value={password} onChange={(e) => setPassword(e.target.value)} minLength={12} required autoComplete="new-password" />
        </label>
        <label className="block">
          <span className="label">نقش</span>
          <select className="field" value={role} onChange={(e) => setRole(e.target.value as "staff" | "owner")}>
            <option value="staff">کارمند (دسترسی‌ها را پایین انتخاب می‌کنید)</option>
            <option value="owner">مالک (همه‌چیز، بدون محدودیت)</option>
          </select>
        </label>
        {role === "staff" && (
          <div className="md:col-span-2">
            <p className="label">این کارمند به کدام بخش‌ها دسترسی داشته باشد؟</p>
            <PermissionPicker catalog={catalog} value={keys} onChange={setKeys} />
          </div>
        )}
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
        <PasswordInput placeholder="رمز فعلی" value={current} onChange={(e) => setCurrent(e.target.value)} required autoComplete="current-password" aria-label="رمز فعلی" />
        <PasswordInput placeholder="رمز جدید (حداقل ۱۲)" value={next} onChange={(e) => setNext(e.target.value)} minLength={12} required autoComplete="new-password" aria-label="رمز جدید" />
        <PasswordInput placeholder="تکرار رمز جدید" value={repeat} onChange={(e) => setRepeat(e.target.value)} minLength={12} required autoComplete="new-password" aria-label="تکرار رمز جدید" />
        {message && <Alert tone={message.tone}>{message.text}</Alert>}
        <button type="submit" disabled={busy} className={buttonClasses("dark", "md", "w-full")}>
          {busy ? <Spinner /> : "تغییر رمز"}
        </button>
      </form>
    </Card>
  );
}
