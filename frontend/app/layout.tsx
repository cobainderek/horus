import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "hórus // fiscalização pública",
  description: "Sistema de cruzamento de bases públicas para detecção de irregularidades em contratos federais",
};

const ASCII_LOGO = `
 ██╗  ██╗ ██████╗ ██████╗ ██╗   ██╗███████╗
 ██║  ██║██╔═══██╗██╔══██╗██║   ██║██╔════╝
 ███████║██║   ██║██████╔╝██║   ██║███████╗
 ██╔══██║██║   ██║██╔══██╗██║   ██║╚════██║
 ██║  ██║╚██████╔╝██║  ██║╚██████╔╝███████║
 ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-br">
      <body className="min-h-screen scanlines">
        <header className="border-b border-border">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-start justify-between gap-6 flex-wrap">
              <div>
                <pre className="text-accent text-[8px] sm:text-[10px] leading-[1.1] select-none">
                  {ASCII_LOGO}
                </pre>
                <div className="mt-2 text-dim text-xs flex items-center gap-2">
                  <span className="text-accent">$</span>
                  <span>sistema de fiscalização pública</span>
                  <span className="text-dim/50">·</span>
                  <span className="text-accent animate-pulse">●</span>
                  <span>online</span>
                </div>
              </div>
              <nav className="flex flex-wrap gap-1 text-xs items-center mt-2">
                <span className="text-dim">[</span>
                <Link href="/" className="text-accent hover:bg-accent/10 px-2 py-0.5">
                  home
                </Link>
                <span className="text-dim">|</span>
                <Link href="/grafo" className="text-fg hover:text-accent hover:bg-accent/10 px-2 py-0.5">
                  grafo
                </Link>
                <span className="text-dim">|</span>
                <a
                  href="http://localhost:8001/docs"
                  target="_blank"
                  rel="noreferrer"
                  className="text-fg hover:text-accent hover:bg-accent/10 px-2 py-0.5"
                >
                  swagger ↗
                </a>
                <span className="text-dim">]</span>
              </nav>
            </div>
          </div>
        </header>
        <main className="px-6 py-6 max-w-7xl mx-auto">{children}</main>
        <footer className="border-t border-border mt-12">
          <div className="max-w-7xl mx-auto px-6 py-4 text-dim text-[11px] leading-relaxed">
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-accent">$</span>
              <span>hórus v0.3</span>
              <span className="text-dim/40">·</span>
              <span>projeto integrador iii</span>
              <span className="text-dim/40">·</span>
              <span>tads/faesa</span>
              <span className="text-dim/40">·</span>
              <span>derek cobain</span>
              <span className="text-dim/40">·</span>
              <span>orientador: prof. howard cruz</span>
            </div>
            <div className="mt-2 text-dim/60">
              <span className="text-accent">{">"}</span> dados de fonte pública: portal da transparência (cgu) · receita federal (brasilapi) · todo código em github · sem mock
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
