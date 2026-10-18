import type { Metadata, Viewport } from "next";
import { Unbounded, Vazirmatn } from "next/font/google";
import { connection } from "next/server";
import { site } from "@/content/site";
import { siteUrl } from "@/lib/server-api";
import "./globals.css";

// TODO: switch to next/font/local once licensed Dana font files are available.
const vazir = Vazirmatn({ subsets: ["arabic", "latin"], variable: "--font-vazir", display: "swap" });
// Latin-only display face for the wordmark, race numbers and readouts; Persian text always uses Vazirmatn.
const unbounded = Unbounded({ subsets: ["latin"], variable: "--font-unbounded", display: "swap" });

const title = `${site.name} | ${site.nameLatin}`;

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: { default: title, template: `%s | ${site.name}` },
  description: site.description,
  applicationName: site.name,
  alternates: { canonical: "/" },
  openGraph: { type: "website", locale: "fa_IR", siteName: site.name, title, description: site.description, url: "/" },
  twitter: { card: "summary", title, description: site.description },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  themeColor: "#0b0c0f",
  colorScheme: "light",
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // Every page is rendered per request so it carries this request's CSP nonce (see src/proxy.ts).
  await connection();
  return (
    <html lang="fa" dir="rtl" className={`${vazir.variable} ${unbounded.variable}`}>
      <body className="flex min-h-svh flex-col font-sans antialiased">{children}</body>
    </html>
  );
}
