"use client";

import dynamic from "next/dynamic";
import { useId, useRef, useState } from "react";
import { ChatIcon, CloseIcon } from "@/components/icons";

// The panel (and its client code) is only downloaded the first time someone opens the chat.
const AssistantPanel = dynamic(() => import("@/components/assistant/assistant-panel").then((module) => module.AssistantPanel), {
  ssr: false,
});

/** Floating chat launcher in the bottom-right corner. */
export function AssistantWidget() {
  const [open, setOpen] = useState(false);
  const [used, setUsed] = useState(false);
  const panelId = useId();
  const launcher = useRef<HTMLButtonElement>(null);

  const hide = () => setOpen(false);
  const close = () => {
    hide();
    launcher.current?.focus();
  };
  const toggle = () => {
    if (open) close();
    else {
      setUsed(true);
      setOpen(true);
    }
  };

  return (
    <>
      {/* Once opened it stays mounted (just hidden), so closing the chat never loses the conversation. */}
      {used && <AssistantPanel id={panelId} open={open} onClose={close} onNavigate={hide} />}
      <button
        ref={launcher}
        type="button"
        onClick={toggle}
        aria-expanded={open}
        aria-controls={used ? panelId : undefined}
        aria-label={open ? "بستن دستیار هوشمند" : "باز کردن دستیار هوشمند"}
        className="assistant-launcher fixed bottom-4 right-3 z-40 inline-flex h-14 items-center gap-2.5 rounded-full bg-ink px-4 font-bold text-white shadow-[0_18px_40px_-12px_rgb(17_17_20/0.55)] transition-all duration-300 ease-out-expo hover:-translate-y-0.5 hover:bg-black active:scale-[0.97] sm:bottom-6 sm:right-6 sm:px-5"
      >
        {open ? <CloseIcon className="h-6 w-6" /> : <ChatIcon className="h-6 w-6" />}
        <span className="hidden sm:inline">دستیار هوشمند</span>
        {!open && <span aria-hidden="true" className="absolute -left-1 -top-1 h-3.5 w-3.5 rounded-full bg-accent ring-2 ring-canvas" />}
      </button>
    </>
  );
}
