"use client";

import { useEffect, useState } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { Card, Kpi, TabHeader } from "@/components/admin/admin-ui";
import { AssistantCache } from "@/components/admin/assistant-cache";
import { AssistantKnowledge } from "@/components/admin/assistant-knowledge";
import { OUTCOME_LABELS } from "@/components/admin/assistant-labels";
import { AssistantReview } from "@/components/admin/assistant-review";
import { Alert } from "@/components/ui/alert";
import { Spinner } from "@/components/ui/spinner";
import { errorMessage } from "@/lib/api";
import { fa, number } from "@/lib/format";
import type { AssistantOverview } from "@/lib/types";

const PERIODS = [7, 30, 90];

const percent = (part: number, whole: number) => (whole === 0 ? "—" : `${fa(Math.round((part / whole) * 100))}٪`);

/** The smart assistant: how it is doing, what to fix, and the answers it keeps. */
export function AssistantTab() {
  const { call } = useAdmin();
  const [days, setDays] = useState(7);
  const [overview, setOverview] = useState<AssistantOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    call<AssistantOverview>("/assistant/overview", { query: { days } })
      .then((result) => {
        if (cancelled) return;
        setOverview(result);
        setError(null);
      })
      .catch((err) => !cancelled && setError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [call, days, version]);

  const unanswered = overview
    ? (overview.by_outcome.insufficient_information ?? 0) +
      (overview.by_outcome.fallback_provider_unavailable ?? 0) +
      (overview.by_outcome.fallback_budget_exhausted ?? 0)
    : 0;
  const votes = overview ? overview.helpful_votes + overview.not_helpful_votes : 0;
  const outcomes = overview ? Object.entries(overview.by_outcome).sort((a, b) => b[1] - a[1]) : [];

  return (
    <div className="space-y-8">
      <TabHeader
        title="دستیار هوشمند"
        lead="عملکرد دستیار، پرسش‌هایی که جواب نگرفته‌اند و پاسخ‌هایی که برای استفادهٔ دوباره ذخیره شده‌اند."
        actions={
          <div className="flex gap-2" role="group" aria-label="بازهٔ زمانی">
            {PERIODS.map((period) => (
              <button
                key={period}
                type="button"
                onClick={() => setDays(period)}
                aria-pressed={days === period}
                className={`rounded-full border px-4 py-2 text-sm font-bold ${days === period ? "border-ink bg-ink text-on-carbon" : "border-line-strong"}`}
              >
                {fa(period)} روز
              </button>
            ))}
          </div>
        }
      />
      {error && <Alert tone="error">{error}</Alert>}
      {!overview && !error && <Spinner className="h-8 w-8" />}
      {overview && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Kpi label="پرسش‌ها" value={fa(overview.questions)} note={`در ${fa(overview.days)} روز گذشته`} tone="dark" />
            <Kpi
              label="بدون پاسخ"
              value={fa(unanswered)}
              note={`${percent(unanswered, overview.questions)} پرسش‌ها؛ این‌ها را بخوانید`}
              tone={unanswered > 0 ? "accent" : "default"}
            />
            <Kpi
              label="از پاسخ ذخیره‌شده"
              value={percent(overview.served_from_cache, overview.questions)}
              note={`${fa(overview.served_from_cache)} پرسش بدون صدا زدن مدل`}
            />
            <Kpi
              label="رضایت مشتری"
              value={votes === 0 ? "—" : percent(overview.helpful_votes, votes)}
              note={`${fa(overview.helpful_votes)} مفید، ${fa(overview.not_helpful_votes)} مفید نبود`}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card title="نتیجهٔ پرسش‌ها">
              {outcomes.length === 0 ? (
                <p className="text-fg-muted">در این بازه پرسشی ثبت نشده است.</p>
              ) : (
                <ul className="space-y-3">
                  {outcomes.map(([outcome, count]) => (
                    <li key={outcome}>
                      <div className="mb-1 flex justify-between text-sm">
                        <span className="font-bold">{OUTCOME_LABELS[outcome] ?? outcome}</span>
                        <span className="text-fg-muted">{fa(count)}</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-surface-2">
                        <div className="h-full rounded-full bg-accent" style={{ width: `${(count / overview.questions) * 100}%` }} />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card title="مصرف و ذخیره">
              <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                <dt className="text-fg-muted">توکن ورودی</dt>
                <dd className="font-bold">{number(overview.prompt_tokens)}</dd>
                <dt className="text-fg-muted">توکن خروجی</dt>
                <dd className="font-bold">{number(overview.completion_tokens)}</dd>
                <dt className="text-fg-muted">پاسخ‌های ذخیره‌شدهٔ فعال</dt>
                <dd className="font-bold">
                  {fa(overview.cached_answers_active)} از {fa(overview.cached_answers_total)}
                </dd>
                <dt className="text-fg-muted">متن‌های دانش منتشرشده</dt>
                <dd className="font-bold">{fa(overview.knowledge_entries)}</dd>
              </dl>
              <p className="mt-4 text-xs leading-6 text-fg-subtle">
                سقف روزانهٔ توکن و مدل از فایل <span dir="ltr">.env</span> خوانده می‌شود و از این صفحه عوض نمی‌شود.
              </p>
            </Card>
          </div>
        </>
      )}

      <AssistantReview />
      <AssistantCache onChanged={() => setVersion((v) => v + 1)} />
      <AssistantKnowledge onChanged={() => setVersion((v) => v + 1)} />
    </div>
  );
}
