import { headers } from "next/headers";
import { AssistantWidget } from "@/components/assistant/assistant-widget";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export default async function SiteLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // Set by src/proxy.ts: which host this page is served on, so shared links point to the right one.
  const onBookingHost = (await headers()).get("x-davos-host") === "booking";
  return (
    <>
      <a href="#main" className="skip-link">
        پرش به محتوای اصلی
      </a>
      <SiteHeader onBookingHost={onBookingHost} />
      <main id="main" className="flex-1">
        {children}
      </main>
      <SiteFooter onBookingHost={onBookingHost} />
      <AssistantWidget />
    </>
  );
}
