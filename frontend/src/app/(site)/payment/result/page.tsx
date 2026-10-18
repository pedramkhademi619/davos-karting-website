import type { Metadata } from "next";
import { Suspense } from "react";
import { PaymentResult } from "@/components/booking/payment-result";
import { Spinner } from "@/components/ui/spinner";

export const metadata: Metadata = {
  title: "نتیجه پرداخت",
  robots: { index: false, follow: false },
};

export default function PaymentResultPage() {
  return (
    <section className="container-page py-14 md:py-20">
      <Suspense
        fallback={
          <div className="grid min-h-[40vh] place-items-center">
            <Spinner label="در حال بررسی پرداخت" className="h-9 w-9" />
          </div>
        }
      >
        <PaymentResult />
      </Suspense>
    </section>
  );
}
