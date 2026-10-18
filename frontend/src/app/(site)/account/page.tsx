import type { Metadata } from "next";
import { AccountApp } from "@/components/account/account-app";
import { PageHero } from "@/components/page-hero";

export const metadata: Metadata = {
  title: "حساب من",
  robots: { index: false, follow: false },
};

export default function AccountPage() {
  return (
    <>
      <PageHero eyebrow="حساب من" title="بلیت‌ها و اطلاعات من" />
      <section className="container-page py-12 md:py-16">
        <AccountApp />
      </section>
    </>
  );
}
