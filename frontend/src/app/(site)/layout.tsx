import { cookies, headers } from "next/headers";
import { AssistantWidget } from "@/components/assistant/assistant-widget";
import { Intro } from "@/components/intro";
import { MobileCta } from "@/components/mobile-cta";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { getBookingInfo } from "@/lib/server-api";
import { hrefFor } from "@/lib/urls";

export default async function SiteLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // Set by src/proxy.ts: which host this page is served on, so shared links point to the right one.
  const onBookingHost = (await headers()).get("x-davos-host") === "booking";
  // The start-lights intro plays once per browser session (components/intro.tsx sets the cookie).
  const showIntro = !(await cookies()).has("davos_intro");
  const info = await getBookingInfo(); // cached in the server process; the footer shows the shifts from it
  return (
    <div className="theme-carbon" data-intro={showIntro ? "" : undefined}>
      {showIntro && <Intro />}
      <a href="#main" className="skip-link">
        پرش به محتوای اصلی
      </a>
      <SiteHeader onBookingHost={onBookingHost} />
      <main id="main" className="flex-1">
        {children}
      </main>
      <SiteFooter onBookingHost={onBookingHost} info={info} />
      <MobileCta bookingHref={hrefFor("/booking", onBookingHost)} onBookingHost={onBookingHost} />
      <AssistantWidget />
    </div>
  );
}
