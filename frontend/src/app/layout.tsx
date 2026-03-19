import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Chatbot from "@/components/layout/Chatbot";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Maria Mendieta — Finances",
  description: "Personal finance dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Lora:wght@400;500;600&family=Source+Sans+3:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <Providers>
          <Sidebar />
          <main className="ml-60 min-h-screen p-8">{children}</main>
          <Chatbot />
        </Providers>
      </body>
    </html>
  );
}
