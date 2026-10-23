import { ButtonLink } from "@/components/button-link";
import { FaqList } from "@/components/faq-list";
import { SectionHeading } from "@/components/section-heading";
import type { FaqItem } from "@/content/faq";

export function FaqPreview({ items }: { items: readonly FaqItem[] }) {
  return (
    <section className="container-page py-24 md:py-32">
      <div className="grid gap-14 lg:grid-cols-12 lg:gap-20">
        <div className="lg:col-span-5">
          <SectionHeading
            eyebrow="سوالات متداول"
            title="قبل از رزرو، اینا رو بدونید"
            lead="جواب سوال‌هایی که بیشتر از همه می‌پرسن. اگه سوال دیگه‌ای دارید، از دستیار بپرسید یا زنگ بزنید."
          />
          <ButtonLink href="/faq" variant="ghost" className="mt-10">
            همه‌ی سوال‌ها
          </ButtonLink>
        </div>
        <div className="lg:col-span-7">
          <FaqList items={items.slice(0, 4)} />
        </div>
      </div>
    </section>
  );
}
