import type { Metadata } from "next";
import { Courier_Prime, Geist, Geist_Mono, IBM_Plex_Sans } from "next/font/google";
import { THEME_INIT_SCRIPT } from "@/lib/theme";
import "./globals.css";

const display = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["300", "400"],
  variable: "--font-ibm",
});

const sans = Geist({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-geist",
});

const mono = Geist_Mono({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-geist-mono",
});

const pixel = Courier_Prime({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-courier",
});

export const metadata: Metadata = {
  title: "JS SEO. Check one page.",
  description: "Paste a public URL. JS SEO reads the HTML the server sends and lists what to fix first.",
  metadataBase: new URL("https://jslabs.xyz"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      data-theme="light"
      suppressHydrationWarning
      className={`${display.variable} ${sans.variable} ${mono.variable} ${pixel.variable}`}
    >
      <head>
        <meta name="theme-color" content="#F5F4F0" />
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-screen bg-paper font-sans text-ink antialiased">{children}</body>
    </html>
  );
}
