import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Hórus — fiscalização pública",
  description: "Sistema de fiscalização de dados públicos brasileiros",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-br">
      <body className="min-h-screen">
        <header className="border-b border-border px-6 py-4 flex items-center justify-between">
          <div>
            <Link href="/" className="text-accent text-lg font-bold tracking-tight">
              hórus
            </Link>
            <span className="ml-3 text-dim text-xs">
              ./fiscalização_pública
            </span>
          </div>
          <nav className="flex gap-5 text-sm">
            <Link href="/" className="text-fg hover:text-accent">dashboard</Link>
            <Link href="/grafo" className="text-fg hover:text-accent">grafo</Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-dim hover:text-accent"
            >
              swagger ↗
            </a>
          </nav>
        </header>
        <main className="px-6 py-6 max-w-7xl mx-auto">{children}</main>
        <footer className="border-t border-border px-6 py-4 text-dim text-xs">
          hórus &middot; projeto integrador iii &middot; tads/faesa &middot; derek cobain
        </footer>
      </body>
    </html>
  );
}
