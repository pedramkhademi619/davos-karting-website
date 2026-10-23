import type { Metadata } from "next";
import { privateMetadata } from "@/lib/seo";
import { Suspense } from "react";
import { PaymentResult } from "@/components/booking/payment-result";
import { PageSkeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = privateMetadata("نتیجه پرداخت");

export default function PaymentResultPage() {
  return (
    <section className="container-page py-14 md:py-20">
      <Suspense
        fallback={
          <PageSkeleton variant="form" label="در حال بررسی پرداخت" />
        }
      >
        <PaymentResult />
      </Suspense>
    </section>
  );
}
