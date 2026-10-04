"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card } from "@/components/admin/admin-ui";
import { SOURCE_TYPE_LABELS } from "@/components/admin/assistant-labels";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { dateTime, fa } from "@/lib/format";
import type { KnowledgeCatalog, KnowledgeEntry } from "@/lib/types";

const MAX_BODY = 4000;
/** Their titles find the quick answers (hours, booking, prices...), so renaming one turns that shortcut off. */
const QUICK_TITLES = ["ساعت کاری", "نحوه رزرو نوبت", "خودروها و ظرفیت هر سانس", "قیمت‌ها", "باشگاه مشتریان داوس"];

type Draft = { id: string | null; source_type: string; title: string; body: string; url: string };

const EMPTY: Draft = { id: null, source_type: "faq", title: "", body: "", url: "/faq" };

/** What the assistant may answer from. Stored in the database; the owner adds, edits and deletes here. */
export function AssistantKnowledge({ onChanged }: { onChanged: () => void }) {
  const { call, isOwner } = useAdmin();
  const [catalog, setCatalog] = useState<KnowledgeCatalog | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    call<KnowledgeCatalog>("/assistant/knowledge")
      .then((result) => !cancelled && setCatalog(result))
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, version]);

  function edit(entry: KnowledgeEntry) {
    setError(null);
    setDraft({ id: entry.entry_id, source_type: entry.source_type, title: entry.title, body: entry.body, url: entry.url });
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setSaving(true);
    setError(null);
    const body = { source_type: draft.source_type, title: draft.title, body: draft.body, url: draft.url };
    try {
      if (draft.id) await call(`/assistant/knowledge/${draft.id}`, { method: "PUT", body });
      else await call("/assistant/knowledge", { method: "POST", body });
      setDraft(null);
      setVersion((v) => v + 1);
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function remove(entry: KnowledgeEntry) {
    if (!window.confirm(`«${entry.title}» حذف شود؟ دستیار دیگر از این متن جواب نمی‌دهد.`)) return;
    try {
      await call(`/assistant/knowledge/${entry.entry_id}`, { method: "DELETE" });
      setVersion((v) => v + 1);
      onChanged();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <Card title="دانسته‌های دستیار">
      <p className="mb-4 max-w-3xl text-sm leading-7 text-fg-muted">
        دستیار فقط از همین متن‌ها جواب می‌دهد و هر تغییر همان لحظه اعمال می‌شود؛ پاسخ‌های ذخیره‌شده‌ای که از متن قدیمی ساخته شده بودند
        خودکار کنار می‌روند (پاسخ‌هایی که خودتان نوشته یا تأیید کرده‌اید می‌مانند). قیمت، تعداد خودرو و روزهای بدون رزرو را اینجا ننویسید؛
        آن‌ها زنده از «تنظیمات و قیمت‌ها» خوانده می‌شوند.
      </p>
      {error && (
        <Alert tone="error" className="mb-4">
          {error}
        </Alert>
      )}
      {!catalog && !error && <Spinner className="h-7 w-7" />}
      {catalog && (
        <>
          <Alert tone={catalog.sent_whole ? "success" : "warning"} className="mb-5">
            {fa(catalog.entries.length)} متن از حداکثر {fa(catalog.max_entries)}، و {fa(catalog.total_chars)} نویسه از {fa(catalog.max_chars)}.{" "}
            {catalog.sent_whole
              ? "همهٔ متن‌ها با هر پرسش برای دستیار فرستاده می‌شود و پرسش‌های محاوره‌ای هم جواب می‌گیرند."
              : "از این حجم بیشتر، دستیار دیگر همهٔ متن‌ها را نمی‌فرستد و فقط متن‌هایی را پیدا می‌کند که کلماتشان با پرسش یکی باشد؛ پرسش‌های محاوره‌ای ممکن است بی‌جواب بمانند. متن‌ها را کوتاه یا ادغام کنید."}
          </Alert>

          {isOwner && !draft && (
            <button
              type="button"
              className={buttonClasses("dark", "sm", "mb-5")}
              onClick={() => {
                setError(null);
                setDraft(EMPTY);
              }}
            >
              افزودن متن جدید
            </button>
          )}

          {draft && (
            <form onSubmit={save} className="mb-6 space-y-4 rounded-2xl border border-line-strong bg-surface-2 p-4 md:p-5">
              <h3 className="font-black">{draft.id ? "ویرایش متن" : "متن جدید"}</h3>
              <div className="grid gap-4 md:grid-cols-3">
                <label className="block md:col-span-2">
                  <span className="mb-1 block text-sm font-bold">عنوان (کنار پاسخ به‌عنوان منبع دیده می‌شود)</span>
                  <input className="field" required maxLength={300} value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
                </label>
                <label className="block">
                  <span className="mb-1 block text-sm font-bold">نوع</span>
                  <select className="field" value={draft.source_type} onChange={(e) => setDraft({ ...draft, source_type: e.target.value })}>
                    {Object.entries(SOURCE_TYPE_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <label className="block">
                <span className="mb-1 block text-sm font-bold">صفحهٔ مرتبط در سایت (باید با / شروع شود)</span>
                <input className="field" dir="ltr" required maxLength={300} value={draft.url} onChange={(e) => setDraft({ ...draft, url: e.target.value })} />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm font-bold">
                  متن ({fa(draft.body.length)} از {fa(MAX_BODY)})
                </span>
                <textarea className="field" rows={7} required maxLength={MAX_BODY} value={draft.body} onChange={(e) => setDraft({ ...draft, body: e.target.value })} />
              </label>
              {QUICK_TITLES.includes(renamedAwayFrom(catalog, draft)) && (
                <Alert tone="warning">
                  این عنوان برای پاسخ سریع به سؤال‌های ساده (ساعت کاری، رزرو، قیمت، ظرفیت، باشگاه) استفاده می‌شود؛ اگر عوضش کنید آن میان‌بر خاموش
                  می‌شود و پرسش به مدل می‌رسد.
                </Alert>
              )}
              <div className="flex gap-3">
                <button type="submit" disabled={saving} className={buttonClasses("dark", "sm")}>
                  {saving ? "در حال ذخیره…" : "ذخیره"}
                </button>
                <button type="button" onClick={() => setDraft(null)} className={buttonClasses("ghost", "sm")}>
                  انصراف
                </button>
              </div>
            </form>
          )}

          {catalog.entries.length === 0 ? (
            <p className="text-fg-muted">هنوز متنی نیست؛ تا متنی اضافه نکنید دستیار چیزی برای گفتن ندارد.</p>
          ) : (
            <ul className="space-y-3">
              {catalog.entries.map((entry) => (
                <li key={entry.entry_id} className="rounded-2xl border border-line bg-surface p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-black">{entry.title}</h3>
                      <p className="mt-1 text-xs text-fg-subtle">
                        {SOURCE_TYPE_LABELS[entry.source_type] ?? entry.source_type} ·{" "}
                        <span dir="ltr">{entry.url}</span> · {fa(entry.body.length)} نویسه · {dateTime(entry.updated_at)}
                      </p>
                    </div>
                    {isOwner && (
                      <span className="flex gap-4">
                        <button type="button" onClick={() => edit(entry)} className="text-xs font-bold underline">
                          ویرایش
                        </button>
                        <button type="button" onClick={() => remove(entry)} className="text-xs font-bold text-signal underline">
                          حذف
                        </button>
                      </span>
                    )}
                  </div>
                  <p className="mt-3 whitespace-pre-line text-sm leading-7 text-fg-muted">{entry.body}</p>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </Card>
  );
}

/** The stored title of the entry being edited when the form now says something else, otherwise an empty string. */
function renamedAwayFrom(catalog: KnowledgeCatalog, draft: Draft): string {
  const stored = catalog.entries.find((e) => e.entry_id === draft.id);
  return stored && stored.title !== draft.title ? stored.title : "";
}
