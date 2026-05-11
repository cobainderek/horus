"use client";

import { useState } from "react";

import { fmtBRL, type Caso, type Classificacao } from "@/lib/api";

const CLASSIFICACAO = {
  GRAVE: {
    label: "GRAVE",
    descricao: "sanção vigente + contrato ativo agora",
    borda: "border-l-4 border-l-red-500",
    badge: "bg-red-900/40 border-red-500 text-red-300",
  },
  VIGILANCIA: {
    label: "VIGILANCIA",
    descricao: "sanção encerrada, mas contratou enquanto estava punida",
    borda: "border-l-4 border-l-orange-500",
    badge: "bg-orange-900/30 border-orange-500 text-orange-300",
  },
  POTENCIAL: {
    label: "POTENCIAL",
    descricao: "no CEIS, sem sobreposição temporal comprovada",
    borda: "border-l-4 border-l-yellow-700/50",
    badge: "bg-yellow-900/20 border-yellow-700 text-yellow-500",
  },
} satisfies Record<Classificacao, { label: string; descricao: string; borda: string; badge: string }>;

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
  const cls = CLASSIFICACAO[caso.classificacao];

  return (
    <article className={`bg-card border border-border p-5 ${cls.borda}`}>
      {/* CABEÇALHO */}
      <header className="flex items-start justify-between gap-4 pb-4 border-b border-border">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="text-dim text-[10px] uppercase tracking-wider font-mono">
              <span className="text-accent">{">"}</span> caso {String(indice).padStart(3, "0")}
            </span>
            <span
              className={`inline-block px-2 py-0.5 border text-[10px] uppercase tracking-wider font-mono ${cls.badge}`}
              title={cls.descricao}
            >
              [{cls.label}]
            </span>
            {caso.n_smoking_gun > 0 && (
              <span className="inline-block px-2 py-0.5 border border-red-600 bg-red-900/40 text-red-300 text-[10px] uppercase tracking-wider font-mono">
                [!] {caso.n_smoking_gun} contrato{caso.n_smoking_gun !== 1 ? "s" : ""} pós-sanção
              </span>
            )}
          </div>
          <h2 className="text-fg text-lg leading-tight font-bold">
            {caso.empresa.razao_social}
          </h2>
          {cadastro?.nome_fantasia && (
            <div className="text-dim text-xs italic mt-0.5">
              <span className="text-accent">{"↪"}</span> "{cadastro.nome_fantasia}"
            </div>
          )}
          <div className="text-dim text-xs mt-1 font-mono">
            <span className="text-dim/60">cnpj</span> {caso.empresa.cnpj}
            {cadastro?.municipio && cadastro?.uf && (
              <>
                <span className="text-dim/40 mx-2">│</span>
                <span>{cadastro.municipio}/{cadastro.uf}</span>
              </>
            )}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-alert text-2xl md:text-3xl font-bold tracking-tight whitespace-nowrap tabular-nums">
            {fmtBRL(caso.valor_total)}
          </div>
          <div className="text-dim text-[10px] uppercase tracking-wider mt-1 font-mono">
            em {caso.n_contratos} contrato{caso.n_contratos !== 1 ? "s" : ""}
          </div>
          {caso.n_aditivos_abusivos > 0 && (
            <div className="text-red-400 text-[10px] uppercase tracking-wider mt-1 font-bold font-mono">
              [!] {caso.n_aditivos_abusivos} aditivo{caso.n_aditivos_abusivos !== 1 ? "s" : ""} abusivo{caso.n_aditivos_abusivos !== 1 ? "s" : ""}
            </div>
          )}
        </div>
      </header>

      {/* SANÇÃO */}
      {sancao && (
        <div className="py-4 border-b border-border">
          <div className="text-accent text-[10px] uppercase tracking-wider mb-2 font-mono">
            {">"} sanção aplicada
          </div>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={`inline-block px-2 py-0.5 border text-[10px] uppercase tracking-wider font-mono ${corSancao(sancao.tipo)}`}>
              {sancao.tipo || "sancionada"}
            </span>
            {sancao.vigente_hoje ? (
              <span className="inline-block px-2 py-0.5 border border-red-500 bg-red-900/30 text-red-300 text-[10px] uppercase tracking-wider font-mono">
                ● em vigor
              </span>
            ) : (
              <span className="inline-block px-2 py-0.5 border border-dim/40 text-dim text-[10px] uppercase tracking-wider font-mono">
                ○ encerrada
              </span>
            )}
            <span className="text-dim text-xs">
              por <span className="text-fg">{sancao.orgao_sancionador || "—"}</span>
            </span>
          </div>
          <div className="text-dim text-xs font-mono">
            <span className="text-dim/60">vigência:</span> {fmtData(sancao.inicio)} → {fmtData(sancao.fim)}
            {caso.sancoes.length > 1 && (
              <span className="ml-2 text-alert">
                [+{caso.sancoes.length - 1} outra{caso.sancoes.length > 2 ? "s" : ""}]
              </span>
            )}
          </div>
          {sancao.numero_processo && (
            <div className="text-dim text-[10px] mt-1 font-mono">
              <span className="text-dim/60">processo:</span> {sancao.numero_processo}
            </div>
          )}
        </div>
      )}

      {/* CONTEXTO DA EMPRESA (BrasilAPI) */}
      {cadastro && (
        <div className="py-4 border-b border-border">
          <button
            onClick={() => setExpandidoEmpresa((v) => !v)}
            className="text-accent text-[10px] uppercase tracking-wider hover:text-fg mb-3 flex items-center gap-2 font-mono"
          >
            <span>[{expandidoEmpresa ? "-" : "+"}]</span>
            {">"} contexto da empresa (receita federal)
          </button>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div>
              <div className="text-dim text-[10px] font-mono">▸ situação</div>
              <div className={`font-bold ${corSituacao(cadastro.situacao_cadastral)}`}>
                {cadastro.situacao_cadastral || "—"}
              </div>
            </div>
            <div>
              <div className="text-dim text-[10px] font-mono">▸ porte</div>
              <div className="text-fg">{cadastro.porte || "—"}</div>
            </div>
            <div>
              <div className="text-dim text-[10px] font-mono">▸ capital social</div>
              <div className="text-fg tabular-nums">{cadastro.capital_social != null ? fmtBRL(cadastro.capital_social) : "—"}</div>
            </div>
            <div>
              <div className="text-dim text-[10px] font-mono">▸ abertura</div>
              <div className="text-fg">{fmtData(cadastro.data_inicio_atividade)}</div>
            </div>
          </div>
          {expandidoEmpresa && (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-3 border-t border-border">
              <div>
                <div className="text-dim text-[10px] mb-0.5 font-mono">▸ atividade (CNAE)</div>
                <div className="text-fg leading-snug">{cadastro.cnae_descricao || "—"}</div>
              </div>
              <div>
                <div className="text-dim text-[10px] mb-0.5 font-mono">▸ natureza jurídica</div>
                <div className="text-fg leading-snug">{cadastro.natureza_juridica || "—"}</div>
                {cadastro.opcao_simples && (
                  <div className="text-yellow-400 text-[10px] mt-1 font-mono">[!] optante do Simples Nacional</div>
                )}
              </div>
              {caso.socios.length > 0 && (
                <div className="md:col-span-2">
                  <div className="text-dim text-[10px] mb-1 font-mono">
                    ▸ sócios e administradores ({caso.socios.length})
                  </div>
                  <ul className="space-y-0.5 font-mono">
                    {caso.socios.map((s, i) => (
                      <li key={i} className="text-fg leading-snug text-xs">
                        <span className="text-accent">{">"}</span> {s.nome}
                        {s.qualificacao && <span className="text-dim text-[10px] ml-2">[{s.qualificacao}]</span>}
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
        <div className="text-accent text-[10px] uppercase tracking-wider mb-3 font-mono">
          {">"} contratos federais
        </div>
        <p className="text-fg text-sm mb-3">
          figura como fornecedor em{" "}
          <span className="text-alert font-bold tabular-nums">{fmtBRL(caso.valor_total)}</span>
          {cadastro && cadastro.capital_social && cadastro.capital_social > 0 ? (
            <span className="text-dim text-xs">
              {" "}({(caso.valor_total / cadastro.capital_social).toFixed(1)}× o capital social)
            </span>
          ) : null}
        </p>

        <ul className="space-y-3 font-mono">
          {caso.contratos.slice(0, limite).map((c) => (
            <li key={c.id} className={`border-l-2 pl-3 ${c.tem_aditivo_abusivo ? "border-red-500" : "border-alert/40"}`}>
              <div className="flex justify-between items-baseline gap-3">
                <span className="text-accent text-sm font-bold">
                  <span className="text-dim/60">▸</span> {c.orgao}
                </span>
                <span className="text-alert text-sm whitespace-nowrap tabular-nums font-bold">
                  {fmtBRL(c.valor)}
                </span>
              </div>
              {c.tem_aditivo_abusivo && (
                <div className="text-red-400 text-[10px] mt-1 font-bold">
                  [!] aditivo abusivo: {fmtBRL(c.valor_inicial || 0)} → {fmtBRL(c.valor_final || c.valor)} (+{c.crescimento_pct?.toFixed(0)}%)
                </div>
              )}
              <p className="text-dim text-xs mt-1 leading-snug">{objetoCurto(c.objeto)}</p>
              <div className="text-dim text-[10px] mt-1 flex gap-3 flex-wrap">
                <span>vigência {fmtData(c.data_inicio)} → {fmtData(c.data_fim)}</span>
                {c.modalidade && <span>│ modalidade: {c.modalidade}</span>}
              </div>
            </li>
          ))}
        </ul>

        {caso.contratos.length > 3 && (
          <button
            onClick={() => setExpandidoContratos((v) => !v)}
            className="text-accent text-xs mt-3 hover:underline font-mono"
          >
            [{expandidoContratos ? "-" : "+"}] {expandidoContratos
              ? "recolher"
              : `ver mais ${caso.contratos.length - 3} contrato${caso.contratos.length - 3 !== 1 ? "s" : ""}`}
          </button>
        )}
      </div>

      <footer className="mt-4 pt-3 border-t border-border">
        <div className="text-dim text-[10px] uppercase tracking-wider mb-2 font-mono">
          {">"} verificar nas fontes
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs font-mono">
          <a
            href={caso.links_verificacao.ceis}
            target="_blank"
            rel="noreferrer"
            className="text-accent hover:underline"
          >
            [link] sanção CEIS ↗
          </a>
          <a
            href={caso.links_verificacao.portal_empresa}
            target="_blank"
            rel="noreferrer"
            className="text-accent hover:underline"
          >
            [link] página da empresa ↗
          </a>
          {caso.links_verificacao.dou && (
            <a
              href={caso.links_verificacao.dou}
              target="_blank"
              rel="noreferrer"
              className="text-accent hover:underline"
            >
              [link] DOU ↗
            </a>
          )}
          {caso.links_verificacao.google && (
            <a
              href={caso.links_verificacao.google}
              target="_blank"
              rel="noreferrer"
              className="text-dim hover:text-accent"
            >
              [link] google ↗
            </a>
          )}
          <span className="ml-auto text-dim/60">{caso.empresa.cnpj}</span>
        </div>
      </footer>
    </article>
  );
}
