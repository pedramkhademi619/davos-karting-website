import { ButtonLink } from "@/components/button-link";
import { FaqList } from "@/components/faq-list";
import { SectionHeading } from "@/components/section-heading";
import { faqItems } from "@/content/site";

export function FaqPreview() {
  return (
    <section className="container-page pb-24 md:pb-36">
      <div className="grid gap-14 lg:grid-cols-12 lg:gap-20">
        <div className="lg:col-span-5">
          <SectionHeading
            eyebrow="سوالات متداول"
            title="پیش از رزرو، این‌ها را بدانید"
            lead="پاسخ رایج‌ترین پرسش‌ها؛ اگر چیز دیگری می‌خواهید بدانید، با ما در تماس باشید."
          />
          <ButtonLink href="/faq" variant="ghost" className="mt-10">
            مشاهده همه سوالات
          </ButtonLink>
        </div>
        <div className="lg:col-span-7">
          <FaqList items={faqItems.slice(0, 3)} />
        </div>
      </div>
    </section>
  );
}
