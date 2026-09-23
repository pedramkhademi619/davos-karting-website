"use client";

import Link from "next/link";
import { type KeyboardEvent, useEffect, useRef, useState } from "react";
import { CloseIcon, SendIcon } from "@/components/icons";
import { assistantSuggestions } from "@/content/site";
import { AssistantError, type AssistantSource, MAX_QUESTION_CHARS, askAssistant, newId, sendFeedback } from "@/lib/assistant-client";

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  sources?: AssistantSource[];
  sourcesLabel?: string;
  suggestTicket?: boolean;
  /** Set only on real answers, which are the only messages that can be rated. */
  interactionId?: string | null;
  feedback?: "up" | "down";
};

const GREETING: Message = {
  id: "greeting",
  role: "assistant",
  text: "سلام! من دستیار داوس هستم. درباره رزرو نوبت و اطلاعات مجموعه از من بپرسید. فقط از اطلاعات تاییدشده همین سایت جواب می‌دهم.",
};
const GENERIC_ERROR = "دستیار الان در دسترس نیست. کمی بعد دوباره امتحان کنید یا از صفحه «تماس با ما» استفاده کنید.";
const TIMEOUT_MS = 45_000;
const MAX_INPUT_HEIGHT = 112;

type AssistantPanelProps = {
  id: string;
  open: boolean;
  onClose: () => void;
  /** Called when a link inside the chat is followed, so the panel does not cover the page that opens. */
  onNavigate: () => void;
};

export function AssistantPanel({ id, open, onClose, onNavigate }: AssistantPanelProps) {
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const conversation = useRef<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  const list = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);

  useEffect(() => {
    list.current?.scrollTo({ top: list.current.scrollHeight });
  }, [messages, pending]);

  useEffect(() => {
    const field = input.current;
    if (!field) return;
    field.style.height = "auto";
    // scrollHeight excludes the border, height includes it: add it back or a 2px overflow makes a scrollbar appear.
    const wanted = field.scrollHeight + (field.offsetHeight - field.clientHeight);
    field.style.height = `${Math.min(wanted, MAX_INPUT_HEIGHT)}px`;
    field.style.overflowY = wanted > MAX_INPUT_HEIGHT ? "auto" : "hidden";
  }, [draft]);

  useEffect(() => () => controller.current?.abort(), []);

  async function send(raw: string) {
    const question = raw.trim().slice(0, MAX_QUESTION_CHARS);
    if (!question || pending) return;
    conversation.current ??= newId();
    setMessages((current) => [...current, { id: newId(), role: "user", text: question }]);
    setDraft("");
    setPending(true);

    const request = new AbortController();
    controller.current = request;
    const timer = setTimeout(() => request.abort(), TIMEOUT_MS);
    try {
      const result = await askAssistant(question, conversation.current, request.signal);
      const answered = result.outcome === "answered";
      setMessages((current) => [
        ...current,
        {
          id: newId(),
          role: "assistant",
          text: result.answer,
          sources: result.sources,
          sourcesLabel: answered ? "منبع" : "مطالب مرتبط",
          suggestTicket: result.suggestTicket,
          interactionId: answered ? result.interactionId : null,
        },
      ]);
    } catch (error) {
      const text = error instanceof AssistantError ? error.message : GENERIC_ERROR;
      setMessages((current) => [...current, { id: newId(), role: "assistant", text }]);
    } finally {
      clearTimeout(timer);
      setPending(false);
    }
  }

  function rate(message: Message, helpful: boolean) {
    if (!message.interactionId || message.feedback) return;
    setMessages((current) => current.map((item) => (item.id === message.id ? { ...item, feedback: helpful ? "up" : "down" } : item)));
    void sendFeedback(message.interactionId, helpful);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void send(draft);
    }
  }

  return (
    <section
      id={id}
      role="dialog"
      aria-label="دستیار هوشمند داوس"
      hidden={!open}
      onKeyDown={(event) => event.key === "Escape" && onClose()}
      className="rise fixed bottom-[5.5rem] right-3 z-40 flex h-[min(34rem,calc(100svh-7rem))] w-[calc(100vw-1.5rem)] max-w-[24rem] flex-col overflow-hidden rounded-3xl border border-line bg-surface shadow-[0_30px_80px_-20px_rgb(17_17_20/0.35)] sm:right-6"
    >
      <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
        <div>
          <p className="flex items-center gap-2 font-black">
            <span aria-hidden="true" className="h-[3px] w-5 rounded-full bg-accent" />
            دستیار هوشمند داوس
          </p>
          <p className="mt-0.5 text-xs text-fg-subtle">پاسخ از روی اطلاعات منتشرشده سایت</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="بستن دستیار"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-line-strong text-fg transition-colors hover:border-fg"
        >
          <CloseIcon className="h-4 w-4" />
        </button>
      </header>

      <div ref={list} role="log" aria-live="polite" aria-relevant="additions" className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-5">
        {messages.map((message) => (
          <div key={message.id} className={`flex max-w-[92%] flex-col gap-2 ${message.role === "user" ? "self-start" : "self-end"}`}>
            <p
              dir="auto"
              className={`whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-[0.95rem] leading-7 ${
                message.role === "user" ? "rounded-ss-md bg-ink text-white" : "rounded-se-md bg-surface-2 text-fg"
              }`}
            >
              {message.text}
            </p>

            {message.sources && message.sources.length > 0 && (
              <p className="px-1 text-xs text-fg-muted">
                {message.sourcesLabel}:{" "}
                {message.sources.map((source, index) => (
                  <span key={source.url + source.title}>
                    {index > 0 && "، "}
                    <Link href={source.url} onClick={onNavigate} className="underline decoration-accent decoration-2 underline-offset-4 hover:text-fg">
                      {source.title}
                    </Link>
                  </span>
                ))}
              </p>
            )}

            {message.suggestTicket && (
              <Link
                href="/contact"
                onClick={onNavigate}
                className="inline-flex w-fit items-center rounded-full border border-fg px-4 py-1.5 text-sm font-bold transition-colors hover:bg-fg hover:text-canvas"
              >
                تماس با ما
              </Link>
            )}

            {message.interactionId && (
              <p className="flex items-center gap-2 px-1 text-xs text-fg-muted">
                {message.feedback ? (
                  "ممنون از بازخورد شما"
                ) : (
                  <>
                    این پاسخ مفید بود؟
                    <button type="button" onClick={() => rate(message, true)} className="rounded-full border border-line-strong px-3 py-0.5 hover:border-fg hover:text-fg">
                      بله
                    </button>
                    <button type="button" onClick={() => rate(message, false)} className="rounded-full border border-line-strong px-3 py-0.5 hover:border-fg hover:text-fg">
                      خیر
                    </button>
                  </>
                )}
              </p>
            )}
          </div>
        ))}

        {messages.length === 1 && (
          <div className="flex flex-wrap gap-2">
            {assistantSuggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => void send(suggestion)}
                className="rounded-full border border-line-strong bg-canvas px-4 py-1.5 text-sm font-medium transition-colors hover:border-fg"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {pending && (
          <div role="status" className="flex w-fit items-center gap-1.5 self-end rounded-2xl rounded-se-md bg-surface-2 px-4 py-3">
            <span className="sr-only">دستیار در حال نوشتن است</span>
            {[0, 1, 2].map((dot) => (
              <span key={dot} aria-hidden="true" className="typing-dot" style={{ "--i": dot } as React.CSSProperties} />
            ))}
          </div>
        )}
      </div>

      <form
        className="border-t border-line px-3 pb-2 pt-3"
        onSubmit={(event) => {
          event.preventDefault();
          void send(draft);
        }}
      >
        <div className="flex items-end gap-2">
          <textarea
            ref={input}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            maxLength={MAX_QUESTION_CHARS}
            dir="auto"
            aria-label="پیام شما"
            placeholder="پرسش خود را بنویسید…"
            className="max-h-28 min-h-11 flex-1 resize-none overflow-hidden rounded-2xl border border-line-strong bg-canvas px-4 py-2.5 text-[0.95rem] leading-6 placeholder:text-fg-subtle"
          />
          <button
            type="submit"
            disabled={pending || !draft.trim()}
            aria-label="ارسال پیام"
            className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-accent text-ink transition-all hover:bg-accent-hover disabled:opacity-40"
          >
            <SendIcon className="h-5 w-5 rtl:-scale-x-100" />
          </button>
        </div>
        <p className="mt-2 px-1 text-[0.7rem] leading-5 text-fg-subtle">
          {draft.length > MAX_QUESTION_CHARS - 100 && (
            <span className="ms-2 float-end tabular-nums">
              {draft.length}/{MAX_QUESTION_CHARS}
            </span>
          )}
          پیام‌ها برای تولید پاسخ به یک سرویس هوش مصنوعی ارسال می‌شود؛ اطلاعات شخصی یا مالی ننویسید.
        </p>
      </form>
    </section>
  );
}
