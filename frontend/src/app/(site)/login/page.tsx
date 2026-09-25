import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginPanel } from "@/components/auth/login-panel";
import { PageHero } from "@/components/page-hero";

export const metadata: Metadata = {
  title: "ورود",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return (
    <>
      <PageHero eyebrow="حساب کاربری" title="ورود به داوس" lead="با شماره موبایل و کد پیامکی وارد شوید؛ حساب شما همان‌جا ساخته می‌شود." />
      <section className="container-page py-12 md:py-16">
        <Suspense fallback={null}>
          <LoginPanel />
        </Suspense>
      </section>
    </>
  );
}
