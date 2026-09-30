import type { Metadata } from "next";
import Link from "next/link";
import { ButtonLink } from "@/components/button-link";
import { Logo } from "@/components/logo";
import { SpeedLines } from "@/components/speed-lines";
import { site } from "@/content/site";

export const metadata: Metadata = {
  title: "صفحه پیدا نشد",
  robots: { index: false },
};

export default function NotFound() {
  return (
    <main className="carbon relative isolate flex min-h-svh flex-col overflow-hidden">
      <SpeedLines />
      <div className="container-page relative py-6">
        <Link href="/" className="rounded-xl">
          <Logo tone="light" />
        </Link>
      </div>
      <div className="container-page relative flex flex-1 flex-col items-start justify-center py-16">
        <p aria-hidden="true" className="race-number text-[clamp(6rem,22vw,14rem)] font-black leading-none text-transparent [-webkit-text-stroke:2px_rgb(255_196_0/0.7)]">
          404
        </p>
        <h1 className="mt-6 text-3xl font-black md:text-5xl">از مسیر خارج شدید!</h1>
        <p className="mt-4 max-w-md text-lg text-on-carbon-muted">صفحه‌ای که دنبالش بودید پیدا نشد. به پیست برگردید.</p>
        <div className="mt-10 flex flex-wrap gap-4">
          <ButtonLink href="/">بازگشت به صفحه اصلی</ButtonLink>
          <ButtonLink href={site.booking.href} variant="ghost-light" arrow={false}>
            {site.booking.callToAction}
          </ButtonLink>
        </div>
      </div>
      <div className="checker" aria-hidden="true" />
    </main>
  );
}
