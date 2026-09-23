import type { Metadata } from "next";
import { ButtonLink } from "@/components/button-link";

export const metadata: Metadata = {
  title: "صفحه پیدا نشد",
};

export default function NotFound() {
  return (
    <section className="relative isolate overflow-hidden">
      <div className="hero-bg" aria-hidden="true" />
      <div className="grain" aria-hidden="true" />
      <div className="container-page flex min-h-[70svh] flex-col items-start justify-center py-24">
        <p aria-hidden="true" className="text-[clamp(6rem,22vw,14rem)] font-black leading-none text-line-strong">
          ۴۰۴
        </p>
        <h1 className="mt-6 text-3xl font-black md:text-5xl">این مسیر به جایی نمی‌رسد</h1>
        <p className="mt-4 max-w-md text-lg text-fg-muted">صفحه‌ای که دنبالش بودید پیدا نشد. به صفحه اصلی برگردید.</p>
        <ButtonLink href="/" className="mt-10">
          بازگشت به صفحه اصلی
        </ButtonLink>
      </div>
    </section>
  );
}
