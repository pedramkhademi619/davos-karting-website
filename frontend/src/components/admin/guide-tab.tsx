"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { useAdmin } from "@/components/admin/admin-session";
import { TabHeader } from "@/components/admin/admin-ui";
import { SendIcon } from "@/components/icons";
import { Skeleton } from "@/components/ui/skeleton";
import { errorMessage } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

const STORAGE_KEY = "davos-panel-guide";
const SUGGESTIONS = [
  "فروش حضوری را چطور ثبت کنم؟",
  "یک خرج تازه را کجا ثبت کنم؟",
  "حقوق کارمند را چطور پرداخت کنم؟",
  "بلیتی را اشتباه ثبت کردم، چه کنم؟",
  "ساعت شیفت صبح را کجا عوض کنم؟",
  "صندوق آخر شب را چطور ببندم؟",
];

function saved(): Message[] {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Message[]) : [];
  } catch {
    return [];
  }
}

/**
 * The panel's own helper: staff ask "how do I do X?" and it answers from a written guide of the whole panel. It is a
 * different assistant from the customers' one (its own prompt, no customer data); the conversation stays in this
 * browser tab only.
 */
export function GuideTab() {
  const { call, me } = useAdmin();
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- restores this tab's conversation after a reload
    setMessages(saved());
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-20)));
    } catch {
      // private window: the conversation just does not survive a reload
    }
  }, [messages, busy]);

  async function ask(question: string) {
    const clean = question.trim();
    if (!clean || busy) return;
    const next: Message[] = [...messages, { role: "user", content: clean }];
    setMessages(next);
    setText("");
    setBusy(true);
    setError(null);
    try {
      const reply = await call<{ answer: string }>("/guide/ask", { method: "POST", body: { messages: next.slice(-10) } });
      setMessages([...next, { role: "assistant", content: reply.answer }]);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void ask(text);
  }

  const first = me.display_name?.split(" ")[0] || "";

  return (
    <div className="mx-auto max-w-3xl">
      <TabHeader
        title="راهنمای پنل"
        lead="هر کاری در پنل بلد نبودید یا گیر کردید، همین‌جا بپرسید؛ مثل همکاری که کنار دستتان نشسته. این دستیار از دستیار مشتری‌ها جداست."
      />
      <div className="panel flex min-h-[28rem] flex-col p-4 md:p-6">
        <div className="flex-1 space-y-4" aria-live="polite">
          {messages.length === 0 && (
            <div className="space-y-5 py-6">
              <p className="text-lg font-black">{first ? `سلام ${first}، چه کمکی از دستم برمی‌آید؟` : "سلام، چه کمکی از دستم برمی‌آید؟"}</p>
              <p className="text-sm leading-7 text-fg-muted">فقط بنویسید چه کاری می‌خواهید بکنید؛ قدم‌به‌قدم می‌گویم کجا بروید و روی کدام دکمه بزنید. اگر چیزی در پنل نبود، راستش را می‌گویم.</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <button key={s} type="button" onClick={() => void ask(s)} className="rounded-full px-4 py-2 text-sm font-bold ring-1 ring-line-strong transition-colors hover:bg-surface-2">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-start" : "justify-end"}`}>
              <p className={`max-w-[88%] whitespace-pre-wrap rounded-3xl px-4 py-3 text-[0.95rem] leading-8 ${m.role === "user" ? "bg-ink text-white" : "bg-surface-2"}`}>{m.content}</p>
            </div>
          ))}
          {busy && (
            <div className="flex justify-end" role="status">
              <span className="sr-only">در حال نوشتن جواب</span>
              <div className="w-3/4 max-w-sm space-y-2 rounded-3xl bg-surface-2 p-4">
                <Skeleton className="h-3 w-full rounded-full" />
                <Skeleton className="h-3 w-5/6 rounded-full" />
                <Skeleton className="h-3 w-2/3 rounded-full" />
              </div>
            </div>
          )}
          {error && <p className="rounded-2xl bg-signal/10 p-3 text-sm font-bold text-signal">{error}</p>}
          <div ref={bottom} />
        </div>
        <form onSubmit={submit} className="mt-5 flex gap-2">
          <input
            className="field flex-1"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={1500}
            placeholder="مثلاً: حقوق علی را چطور بدهم؟"
            aria-label="سؤال شما"
          />
          <button type="submit" disabled={busy || !text.trim()} aria-label="فرستادن" className="grid h-[3.25rem] w-[3.25rem] shrink-0 place-items-center rounded-full bg-accent text-ink disabled:opacity-40">
            <SendIcon className="h-5 w-5" />
          </button>
        </form>
        {messages.length > 0 && (
          <button type="button" onClick={() => setMessages([])} className="mt-3 self-start text-xs font-bold text-fg-subtle underline">
            شروع گفتگوی تازه
          </button>
        )}
      </div>
    </div>
  );
}
