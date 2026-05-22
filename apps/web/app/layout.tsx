import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DiffShield",
  description: "World-model-lite repo threat reviewer"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

