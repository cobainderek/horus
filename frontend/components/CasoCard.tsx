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
  if (t.includes("inidôn") || t.includes("inidon"))
    return "bg-red-900/30 border-red-500 text-red-400";
  if (t.includes("impediment"))
    return "bg-orange-900/30 border-orange-500 text-orange-400";
  if (t.includes("suspens"))
    return "bg-yellow-900/30 border-yellow-600 text-yellow-400";
  return "bg-alert/15 border-alert text-alert";
};

const corSituacao = (s: string | null) => {
  if (!s) return "text-dim";
  if (s.toUpperCase().includes("ATIVA")) return "text-accent";
  return "text-alert";
};

export function CasoCard({ caso, indice }: { caso: Caso; indice: number }) {
  const [expandidoContratos, setExpandidoContratos] = useState(false);
  const [expandidoEmpresa, setExpandidoEmpresa] = useState(false);
  const limite = expandidoContratos ? caso.contratos.length : 3;
  const sancao = caso.sancoes[0];
  const cadastro = caso.cadastro;
  const objetoCurto = (s: string) => (s.length > 200 ? s.slice(0, 197) + "..." : s);

  return (
    <article className="bg-card border border-border rounded p-5">
      {/* CABEÇALHO */}
      <header className="flex items-start justify-between gap-4 pb-4 border-b border-border">
        <div className="min-w-0">
          <div className="text-dim text-[10px] uppercase tracking-wider mb-1">
            caso #{String(indice).padStart(2, "0")}
          </div>
          <h2 className="text-fg text-lg leading-tight font-semibold">
            {caso.empresa.razao_social}
          </h2>
          {cadastro?.nome_fantasia && (
            <div className="text-dim text-xs italic mt-0.5">
              ↪ "{cadastro.nome_fantasia}"
            </div>
          )}
          <div className="text-dim text-xs mt-1 font-mono">
            cnpj {caso.empresa.cnpj}
            {cadastro?.municipio && cadastro?.uf && (
              <span className="ml-2 text-dim/70">
                · {cadastro.municipio}/{cadastro.uf}
              </span>
            )}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-alert text-2xl font-semibold tracking-tight whitespace-nowrap">
            {fmtBRL(caso.valor_total)}
          </div>
          <div className="text-dim text-[10px] uppercase tracking-wider mt-1">
            figura em {caso.n_contratos} contrato{caso.n_contratos !== 1 ? "s" : ""}
          </div>
          {caso.n_aditivos_abusivos > 0 && (
            <div className="text-red-400 text-[10px] uppercase tracking-wider mt-1 font-semibold">
              ⚠ {caso.n_aditivos_abusivos} aditivo{caso.n_aditivos_abusivos !== 1 ? "s" : ""} abusivo{caso.n_aditivos_abusivos !== 1 ? "s" : ""}
            </div>
          )}
        </div>
      </header>

      {/* SANÇÃO */}
      {sancao && (
        <div className="py-4 border-b border-border">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
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

      {/* CONTEXTO DA EMPRESA (BrasilAPI) */}
      {cadastro && (
        <div className="py-4 border-b border-border">
          <button
            onClick={() => setExpandidoEmpresa((v) => !v)}
            className="text-dim text-[10px] uppercase tracking-wider hover:text-accent mb-2 flex items-center gap-2"
          >
            <span>{expandidoEmpresa ? "▴" : "▾"}</span>
            contexto da empresa (receita federal)
          </button>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div>
              <div className="text-dim text-[10px]">situação</div>
              <div className={`font-semibold ${corSituacao(cadastro.situacao_cadastral)}`}>
                {cadastro.situacao_cadastral || "—"}
              </div>
            </div>
            <div>
              <div className="text-dim text-[10px]">porte</div>
              <div className="text-fg">{cadastro.porte || "—"}</div>
            </div>
            <div>
              <div className="text-dim text-[10px]">capital social</div>
              <div className="text-fg">{cadastro.capital_social != null ? fmtBRL(cadastro.capital_social) : "—"}</div>
            </div>
            <div>
              <div className="text-dim text-[10px]">abertura</div>
              <div className="text-fg">{fmtData(cadastro.data_inicio_atividade)}</div>
            </div>
          </div>
          {expandidoEmpresa && (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-3 border-t border-border">
              <div>
                <div className="text-dim text-[10px] mb-0.5">atividade (CNAE)</div>
                <div className="text-fg leading-snug">{cadastro.cnae_descricao || "—"}</div>
              </div>
              <div>
                <div className="text-dim text-[10px] mb-0.5">natureza jurídica</div>
                <div className="text-fg leading-snug">{cadastro.natureza_juridica || "—"}</div>
                {cadastro.opcao_simples && (
                  <div className="text-yellow-400 text-[10px] mt-1">optante do Simples Nacional</div>
                )}
              </div>
              {caso.socios.length > 0 && (
                <div className="md:col-span-2">
                  <div className="text-dim text-[10px] mb-1">
                    sócios e administradores ({caso.socios.length})
                  </div>
                  <ul className="space-y-0.5">
                    {caso.socios.map((s, i) => (
                      <li key={i} className="text-fg leading-snug">
                        • {s.nome}
                        {s.qualificacao && <span className="text-dim text-[10px] ml-2">{s.qualificacao}</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* CONTRATOS */}
      <div className="pt-4">
        <p className="text-fg text-sm mb-3">
          Figura como fornecedor em <span className="text-alert font-semibold">{fmtBRL(caso.valor_total)}</span> de
          contratos federais{cadastro && cadastro.capital_social && cadastro.capital_social > 0 ? (
            <span className="text-dim text-xs">
              {" "}({(caso.valor_total / cadastro.capital_social).toFixed(1)}× o capital social)
            </span>
          ) : null}:
        </p>

        <ul className="space-y-3">
          {caso.contratos.slice(0, limite).map((c) => (
            <li key={c.id} className={`border-l-2 pl-3 ${c.tem_aditivo_abusivo ? "border-red-500" : "border-alert/40"}`}>
              <div className="flex justify-between items-baseline gap-3">
                <span className="text-accent text-sm font-medium">{c.orgao}</span>
                <span className="text-alert text-sm font-mono whitespace-nowrap">
                  {fmtBRL(c.valor)}
                </span>
              </div>
              {c.tem_aditivo_abusivo && (
                <div className="text-red-400 text-[10px] mt-0.5 font-semibold">
                  ⚠ ADITIVO ABUSIVO — começou em {fmtBRL(c.valor_inicial || 0)}, cresceu {c.crescimento_pct?.toFixed(0)}%
                </div>
              )}
              <p className="text-dim text-xs mt-1 leading-snug">{objetoCurto(c.objeto)}</p>
              <div className="text-dim text-[10px] mt-1 flex gap-3 flex-wrap">
                <span>vigência {fmtData(c.data_inicio)} → {fmtData(c.data_fim)}</span>
                {c.modalidade && <span>· {c.modalidade}</span>}
              </div>
            </li>
          ))}
        </ul>

        {caso.contratos.length > 3 && (
          <button
            onClick={() => setExpandidoContratos((v) => !v)}
            className="text-accent text-xs mt-3 hover:underline"
          >
            {expandidoContratos
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
