import { PlusIcon } from "@/components/icons";

type FaqItem = {
  readonly question: string;
  readonly answer: string;
};

/** Accordion built on native <details>: works without JavaScript and is keyboard and screen-reader friendly. */
export function FaqList({ items }: { items: readonly FaqItem[] }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <details key={item.question} className="faq-item panel-soft overflow-hidden transition-shadow open:shadow-[0_24px_48px_-30px_rgb(40_30_0/0.35)]">
          <summary className="group flex items-center justify-between gap-6 px-6 py-5 md:px-7 md:py-6">
            <h3 className="text-lg font-bold md:text-xl">{item.question}</h3>
            <span className="faq-chip grid h-10 w-10 shrink-0 place-items-center rounded-full border border-line-strong bg-surface transition-colors group-hover:border-accent group-hover:bg-accent">
              <PlusIcon className="faq-icon h-5 w-5 transition-transform duration-300" />
            </span>
          </summary>
          <div className="faq-answer max-w-2xl px-6 pb-6 md:px-7">
            <p className="text-fg-muted">{item.answer}</p>
          </div>
        </details>
      ))}
    </div>
  );
}
