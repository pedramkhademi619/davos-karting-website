import type { Metadata } from "next";
import { privateMetadata } from "@/lib/seo";
import { AccountApp } from "@/components/account/account-app";
import { PageHero } from "@/components/page-hero";

export const metadata: Metadata = privateMetadata("حساب من");

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
