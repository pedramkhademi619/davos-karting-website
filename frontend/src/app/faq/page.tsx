import type { Metadata } from "next";
import { ButtonLink } from "@/components/button-link";
import { FaqList } from "@/components/faq-list";
import { PageHero } from "@/components/page-hero";
import { faqItems } from "@/content/site";

export const metadata: Metadata = {
  title: "سوالات متداول",
  description: "پاسخ رایج‌ترین پرسش‌ها پیش از رزرو نوبت در کارتینگ داوس.",
};

export default function FaqPage() {
  return (
    <>
      <PageHero eyebrow="پشتیبانی" title="سوالات متداول" lead="پاسخ رایج‌ترین پرسش‌ها پیش از رزرو نوبت." />

      <section className="container-page py-16 md:py-24">
        <div className="mx-auto max-w-3xl">
          <FaqList items={faqItems} />

          <div className="mt-16 rounded-[2rem] border border-line bg-surface p-8 text-center md:p-14">
            <h2 className="text-2xl font-black md:text-3xl">پاسخ خود را پیدا نکردید؟</h2>
            <p className="mx-auto mt-4 max-w-md text-fg-muted">با ما در تماس باشید؛ خوشحال می‌شویم راهنمایی‌تان کنیم.</p>
            <ButtonLink href="/contact" className="mt-8">
              تماس با ما
            </ButtonLink>
          </div>
        </div>
      </section>
    </>
  );
}
