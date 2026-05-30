import type { Metadata } from "next";
import { IBM_Plex_Sans } from "next/font/google";

import "@/app/globals.css";
import { Toaster, ToastStateProvider } from "@/components/ui/toaster";

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-sans"
});

export const metadata: Metadata = {
  title: "ClearPass AI",
  description: "Zero-retention immigration document verification."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${ibmPlexSans.variable} antialiased text-ink-950`}>
        <ToastStateProvider>
          {children}
          <Toaster />
        </ToastStateProvider>
      </body>
    </html>
  );
}
