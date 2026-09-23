import type { Metadata, Viewport } from "next";
import { Unbounded, Vazirmatn } from "next/font/google";
import { AssistantWidget } from "@/components/assistant/assistant-widget";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { site } from "@/content/site";
import "./globals.css";

// TODO: switch to next/font/local once licensed Dana font files are available.
const vazir = Vazirmatn({ subsets: ["arabic", "latin"], variable: "--font-vazir", display: "swap" });
// Latin-only display face for the wordmark and decorative type; Persian text always uses Vazirmatn.
const unbounded = Unbounded({ subsets: ["latin"], variable: "--font-unbounded", display: "swap" });

const title = `${site.name} | ${site.nameLatin}`;

export const metadata: Metadata = {
  title: { default: title, template: `%s | ${site.name}` },
  description: site.description,
  openGraph: { type: "website", locale: "fa_IR", siteName: site.name, title, description: site.description },
};

export const viewport: Viewport = {
  themeColor: "#f9f7f2",
  colorScheme: "light",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl" className={`${vazir.variable} ${unbounded.variable}`}>
      <body className="flex min-h-svh flex-col font-sans antialiased">
        <a href="#main" className="skip-link">
          پرش به محتوای اصلی
        </a>
        <SiteHeader />
        <main id="main" className="flex-1">
          {children}
        </main>
        <SiteFooter />
        <AssistantWidget />
      </body>
    </html>
  );
}
