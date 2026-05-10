"use client";

import { useState } from "react";

import { fmtBRL, type Caso } from "@/lib/api";

const fmtData = (d: string | null) => {
  if (!d) return "—";
  const [a, m, dia] = d.split("-");
  return dia && m && a ? `${dia}/${m}/${a}` : d;
};

const corSancao = (tipo: string | null | undefined) => {
  const t = (tipo || "").toLowerCase();
  if (t.includes("inidôn") || t.includes("inidon")) {
    return "bg-red-900/30 border-red-500 text-red-400";
  }
  if (t.includes("impediment")) {
    return "bg-orange-900/30 border-orange-500 text-orange-400";
  }
  if (t.includes("suspens")) {
    return "bg-yellow-900/30 border-yellow-600 text-yellow-400";
  }
  return "bg-alert/15 border-alert text-alert";
};

export function CasoCard({ caso, indice }: { caso: Caso; indice: number }) {
  const [expandido, setExpandido] = useState(false);
  const limite = expandido ? caso.contratos.length : 3;
  const sancao = caso.sancoes[0];
  const objetoCurto = (s: string) => (s.length > 200 ? s.slice(0, 197) + "..." : s);

  return (
    <article className="bg-card border border-border rounded p-5">
      <header className="flex items-start justify-between gap-4 pb-4 border-b border-border">
        <div className="min-w-0">
          <div className="text-dim text-[10px] uppercase tracking-wider mb-1">
            caso #{String(indice).padStart(2, "0")}
          </div>
          <h2 className="text-fg text-lg leading-tight font-semibold">
            {caso.empresa.razao_social}
          </h2>
          <div className="text-dim text-xs mt-1 font-mono">
            cnpj {caso.empresa.cnpj}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-alert text-2xl font-semibold tracking-tight whitespace-nowrap">
            {fmtBRL(caso.valor_total)}
          </div>
          <div className="text-dim text-[10px] uppercase tracking-wider mt-1">
            em {caso.n_contratos} contrato{caso.n_contratos !== 1 ? "s" : ""}
          </div>
        </div>
      </header>

      {sancao && (
        <div className="py-4 border-b border-border">
          <div className="flex items-center gap-2 mb-2">
            <span className={`inline-block px-2 py-0.5 border text-[10px] uppercase tracking-wider rounded ${corSancao(sancao.tipo)}`}>
              {sancao.tipo || "sancionada"}
            </span>
            <span className="text-dim text-xs">
              aplicada por <span className="text-fg">{sancao.orgao_sancionador || "—"}</span>
            </span>
          </div>
          <div className="text-dim text-xs">
            vigência: {fmtData(sancao.inicio)} → {fmtData(sancao.fim)}
            {caso.sancoes.length > 1 && (
              <span className="ml-2 text-alert">
                (+{caso.sancoes.length - 1} outra{caso.sancoes.length > 2 ? "s" : ""} sanção)
              </span>
            )}
          </div>
        </div>
      )}

      <div className="pt-4">
        <p className="text-fg text-sm mb-3">
          Mesmo {sancao?.tipo?.toLowerCase().includes("inidôneo") ? "declarada inidônea" : "sancionada"},
          recebeu <span className="text-alert font-semibold">{fmtBRL(caso.valor_total)}</span> em
          contratos federais:
        </p>

        <ul className="space-y-3">
          {caso.contratos.slice(0, limite).map((c) => (
            <li key={c.id} className="border-l-2 border-alert/40 pl-3">
              <div className="flex justify-between items-baseline gap-3">
                <span className="text-accent text-sm font-medium">{c.orgao}</span>
                <span className="text-alert text-sm font-mono whitespace-nowrap">
                  {fmtBRL(c.valor)}
                </span>
              </div>
              <p className="text-dim text-xs mt-1 leading-snug">{objetoCurto(c.objeto)}</p>
              <div className="text-dim text-[10px] mt-1">
                vigência {fmtData(c.data_inicio)} → {fmtData(c.data_fim)}
              </div>
            </li>
          ))}
        </ul>

        {caso.contratos.length > 3 && (
          <button
            onClick={() => setExpandido((v) => !v)}
            className="text-accent text-xs mt-3 hover:underline"
          >
            {expandido
              ? "▴ recolher"
              : `▾ ver mais ${caso.contratos.length - 3} contrato${caso.contratos.length - 3 !== 1 ? "s" : ""}`}
          </button>
        )}
      </div>

      <footer className="mt-4 pt-3 border-t border-border flex justify-between text-xs">
        <a
          href={caso.empresa.link_transparencia}
          target="_blank"
          rel="noreferrer"
          className="text-dim hover:text-accent"
        >
          portal da transparência ↗
        </a>
        <span className="text-dim font-mono">{caso.empresa.cnpj}</span>
      </footer>
    </article>
  );
}
