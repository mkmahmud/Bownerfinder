import type { Metadata } from "next";
// @ts-ignore
import "./globals.css";

import { AppNav } from "@/components/app-nav";

export const metadata: Metadata = {
  title: "Bownerfinder",
  description: "Self-hosted local business decision maker finder",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-background md:flex">
          <AppNav />
          <main className="min-w-0 flex-1 p-4 md:p-8">{children}</main>
        </div>
      </body>
    </html>
  );
}

