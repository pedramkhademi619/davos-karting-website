"use client";

import { useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Pager, Table, cell } from "@/components/admin/admin-ui";
import { OUTCOME_LABELS, PROBLEM_OUTCOMES } from "@/components/admin/assistant-labels";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { dateTime, fa } from "@/lib/format";
import type { AssistantInteraction, Page } from "@/lib/types";

const LIMIT = 20;

type Show = "all" | "unanswered" | "bad";

const FILTERS: { key: Show; label: string }[] = [
  { key: "unanswered", label: "بدون پاسخ" },
  { key: "bad", label: "«مفید نبود» زده‌اند" },
  { key: "all", label: "همه" },
];

/** What customers asked, newest first. Texts exist only for people who agreed to have them kept. */
export function AssistantReview() {
  const { call } = useAdmin();
  const [show, setShow] = useState<Show>("unanswered");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<Page<AssistantInteraction> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const query =
      show === "bad" ? { helpful: "false", limit: LIMIT, offset } : { show: show === "all" ? "all" : "unanswered", limit: LIMIT, offset };
    call<Page<AssistantInteraction>>("/assistant/interactions", { query })
      .then((result) => {
        if (cancelled) return;
        setPage(result);
        setError(null);
      })
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, show, offset]);

  function choose(next: Show) {
    setPage(null);
    setOffset(0);
    setShow(next);
  }

  return (
    <Card title="بررسی پرسش‌ها">
      <p className="mb-4 max-w-3xl text-sm leading-7 text-fg-muted">
        متن پرسش و پاسخ فقط وقتی ذخیره می‌شود که مشتری اجازه داده باشد؛ برای بقیه فقط نتیجه و تعداد توکن دیده می‌شود. پرسش‌های بدون
        پاسخ نشان می‌دهند چه چیزی را باید به فایل‌های دانش (پوشهٔ backend/knowledge) اضافه کنید.
      </p>
      <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="فیلتر پرسش‌ها">
        {FILTERS.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => choose(key)}
            aria-pressed={show === key}
            className={`rounded-full border px-4 py-2 text-sm font-bold ${show === key ? "border-ink bg-ink text-on-carbon" : "border-line-strong"}`}
          >
            {label}
          </button>
        ))}
      </div>
      {error && (
        <Alert tone="error" className="mb-4">
          {error}
        </Alert>
      )}
      {!page ? (
        <Spinner className="h-7 w-7" />
      ) : (
        <>
          <Table head={["زمان", "نتیجه", "پرسش", "پاسخ", "نظر", "توکن"]} empty={page.items.length === 0}>
            {page.items.map((item) => (
              <tr key={item.interaction_id}>
                <td className={cell}>{dateTime(item.occurred_at)}</td>
                <td className={cell}>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-bold ${PROBLEM_OUTCOMES.includes(item.outcome) ? "bg-signal-soft text-[#7a0600]" : "bg-surface-2"}`}
                  >
                    {OUTCOME_LABELS[item.outcome] ?? item.outcome}
                  </span>
                  {item.served_from_cache && <span className="mr-2 text-xs text-fg-subtle">از ذخیره</span>}
                </td>
                <td className="min-w-56 max-w-xs px-4 py-3 align-top leading-7">
                  {item.question_text ?? <span className="text-fg-subtle">ذخیره نشده</span>}
                </td>
                <td className="min-w-56 max-w-sm px-4 py-3 align-top leading-7 text-fg-muted">{item.answer_text ?? "—"}</td>
                <td className={cell}>{item.helpful === null ? "—" : item.helpful ? "مفید" : "مفید نبود"}</td>
                <td className={cell}>{fa(item.tokens)}</td>
              </tr>
            ))}
          </Table>
          <Pager offset={offset} limit={LIMIT} total={page.total} onChange={setOffset} />
        </>
      )}
    </Card>
  );
}
