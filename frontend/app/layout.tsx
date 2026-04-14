import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinSignal",
  description: "S&P 500 Forecast & Drift Monitoring",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
