"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Pager, Table, cell } from "@/components/admin/admin-ui";
import { buttonClasses } from "@/components/button-link";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { dateTime, fa } from "@/lib/format";
import type { CachedAnswer, Page } from "@/lib/types";

const LIMIT = 20;
const MAX_QUESTION = 400;
const MAX_ANSWER = 2000;

type Draft = { id: string | null; question: string; answer: string };

/** Answers kept for reuse. The owner can write one, correct one, retire it or delete it. */
export function AssistantCache({ onChanged }: { onChanged: () => void }) {
  const { call, isOwner } = useAdmin();
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<Page<CachedAnswer> | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    call<Page<CachedAnswer>>("/assistant/cache", { query: { limit: LIMIT, offset } })
      .then((result) => {
        if (cancelled) return;
        setPage(result);
        setError(null);
      })
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, offset, version]);

  function refresh() {
    setVersion((v) => v + 1);
    onChanged();
  }

  async function change(run: () => Promise<unknown>) {
    try {
      await run();
      refresh();
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setSaving(true);
    setError(null);
    const body = { question: draft.question, answer: draft.answer };
    try {
      if (draft.id) await call(`/assistant/cache/${draft.id}`, { method: "PUT", body });
      else await call("/assistant/cache", { method: "POST", body });
      setDraft(null);
      setOffset(0);
      refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  const toggle = (entry: CachedAnswer) =>
    change(() => call(`/assistant/cache/${entry.entry_id}/active`, { method: "POST", body: { active: !entry.is_active } }));

  const remove = (entry: CachedAnswer) => {
    if (!window.confirm("این پاسخ ذخیره‌شده برای همیشه حذف شود؟")) return;
    return change(() => call(`/assistant/cache/${entry.entry_id}`, { method: "DELETE" }));
  };

  return (
    <Card title="پاسخ‌های ذخیره‌شده">
      <p className="mb-4 max-w-3xl text-sm leading-7 text-fg-muted">
        وقتی کسی پرسشی با همان معنی بپرسد، این پاسخ‌ها بدون صدا زدن مدل نمایش داده می‌شوند. پاسخ اشتباه را اصلاح کنید یا غیرفعال کنید.
        پاسخی که خودتان بنویسید یا اصلاح کنید «نوشتهٔ مالک» می‌شود و با عوض شدن متن‌های دانش یا قیمت‌ها کنار نمی‌رود؛ تا وقتی خودتان
        عوضش نکنید همان نمایش داده می‌شود. فقط پرسش‌های عمومی کار می‌کنند: پرسشی که به سن، قد، روز، ساعت یا تعداد نفرات بستگی دارد
        هیچ‌وقت از پاسخ ذخیره‌شده جواب نمی‌گیرد.
      </p>
      {error && (
        <Alert tone="error" className="mb-4">
          {error}
        </Alert>
      )}

      {isOwner && !draft && (
        <button type="button" className={buttonClasses("dark", "sm", "mb-5")} onClick={() => setDraft({ id: null, question: "", answer: "" })}>
          نوشتن پاسخ جدید
        </button>
      )}
      {draft && (
        <form onSubmit={save} className="mb-6 space-y-4 rounded-2xl border border-line-strong bg-surface-2 p-4 md:p-5">
          <h3 className="font-black">{draft.id ? "اصلاح پاسخ" : "پاسخ جدید"}</h3>
          <label className="block">
            <span className="mb-1 block text-sm font-bold">
              پرسش ({fa(draft.question.length)} از {fa(MAX_QUESTION)})
            </span>
            <input className="field" required maxLength={MAX_QUESTION} value={draft.question} onChange={(e) => setDraft({ ...draft, question: e.target.value })} />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-bold">
              پاسخ ({fa(draft.answer.length)} از {fa(MAX_ANSWER)})
            </span>
            <textarea className="field" rows={5} required maxLength={MAX_ANSWER} value={draft.answer} onChange={(e) => setDraft({ ...draft, answer: e.target.value })} />
          </label>
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

      {!page ? (
        <Spinner className="h-7 w-7" />
      ) : (
        <>
          <Table head={["پرسش", "پاسخ", "تعداد استفاده", "آخرین استفاده", "وضعیت", ""]} empty={page.items.length === 0}>
            {page.items.map((entry) => (
              <tr key={entry.entry_id}>
                <td className="min-w-48 max-w-xs px-4 py-3 align-top font-bold leading-7">{entry.question}</td>
                <td className="min-w-64 max-w-md px-4 py-3 align-top leading-7 text-fg-muted">{entry.answer}</td>
                <td className={cell}>{fa(entry.hit_count)}</td>
                <td className={cell}>{dateTime(entry.last_used_at)}</td>
                <td className={cell}>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-bold ${entry.is_active ? "bg-go-soft text-[#064d29]" : "bg-signal-soft text-[#7a0600]"}`}
                  >
                    {entry.is_active ? "فعال" : "غیرفعال"}
                  </span>
                  {entry.is_curated && <span className="mr-2 text-xs font-bold text-fg-muted">نوشتهٔ مالک</span>}
                </td>
                <td className={cell}>
                  {isOwner && (
                    <span className="flex gap-4">
                      <button
                        type="button"
                        onClick={() => setDraft({ id: entry.entry_id, question: entry.question, answer: entry.answer })}
                        className="text-xs font-bold underline"
                      >
                        اصلاح
                      </button>
                      <button type="button" onClick={() => toggle(entry)} className="text-xs font-bold underline">
                        {entry.is_active ? "غیرفعال کردن" : "فعال کردن"}
                      </button>
                      <button type="button" onClick={() => remove(entry)} className="text-xs font-bold text-signal underline">
                        حذف
                      </button>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </Table>
          <Pager offset={offset} limit={LIMIT} total={page.total} onChange={setOffset} />
        </>
      )}
    </Card>
  );
}
