"use client";

import { useState } from "react";

const SANCOES = [
  {
    tipo: "Impedimento",
    cor: "bg-orange-900/30 border-orange-500 text-orange-400",
    barra: "border-l-orange-500",
    resumo: "Proibição temporária de contratar com a Administração Pública",
    descricao:
      "A empresa é impedida de licitar e contratar com a União por um prazo determinado (normalmente de 6 meses a 2 anos). Geralmente aplicado por descumprimento de contrato anterior, atraso na entrega, fraude em licitação, ou apresentação de documentos falsos.",
    base_legal: "Lei 14.133/2021, art. 156 (Nova Lei de Licitações)",
    quem_aplica: "Órgão contratante (federal, estadual ou municipal)",
    gravidade: 2,
  },
  {
    tipo: "Suspensão",
    cor: "bg-yellow-900/30 border-yellow-600 text-yellow-400",
    barra: "border-l-yellow-600",
    resumo: "Suspensão temporária de participação em licitação",
    descricao:
      "Mais sério que o impedimento. A empresa fica suspensa de participar de licitações por até 2 anos. Aplicado quando há prática de ato lesivo: corrupção, fraude, conluio entre licitantes, ou descumprimento grave.",
    base_legal: "Lei 8.666/93 art. 87 + Lei 14.133/2021",
    quem_aplica: "Órgão contratante, TCU, ou tribunal de contas estadual",
    gravidade: 3,
  },
  {
    tipo: "Declaração de Inidoneidade",
    cor: "bg-red-900/30 border-red-500 text-red-400",
    barra: "border-l-red-500",
    resumo: "Empresa considerada inidônea — proibição geral",
    descricao:
      "A punição mais grave. A empresa é declarada 'não confiável' para contratar com QUALQUER órgão público (federal, estadual, municipal). Pode ser com prazo (geralmente 2 a 5 anos) ou sem prazo definido. Para sair do cadastro, precisa reabilitação.",
    base_legal: "Lei 8.666/93 art. 87 IV + Lei 12.846/13 art. 22",
    quem_aplica: "Ministros de Estado, CGU, AGU, TCU",
    gravidade: 4,
  },
];

export function GlossarioSancoes() {
  const [aberto, setAberto] = useState(false);

  return (
    <div className="bg-card border border-border rounded">
      <button
        onClick={() => setAberto((v) => !v)}
        className="w-full flex items-center justify-between p-4 hover:bg-bg/40 transition"
      >
        <div className="flex items-center gap-3">
          <span className="text-accent text-base">?</span>
          <div className="text-left">
            <div className="text-fg text-sm font-medium">
              o que é "empresa sancionada"?
            </div>
            <div className="text-dim text-xs mt-0.5">
              entenda os tipos de punição, base legal e gravidade
            </div>
          </div>
        </div>
        <span className="text-dim text-xs">{aberto ? "▴ fechar" : "▾ abrir"}</span>
      </button>

      {aberto && (
        <div className="p-5 pt-2 border-t border-border space-y-4">
          <p className="text-fg text-sm leading-relaxed">
            <span className="text-accent">Sanção</span> = punição aplicada pelo
            governo a uma empresa que cometeu irregularidade (fraude, corrupção,
            descumprimento de contrato, etc). A lista oficial é o{" "}
            <strong className="text-fg">CEIS</strong> (Cadastro de Empresas
            Inidôneas e Suspensas), mantido pela{" "}
            <strong className="text-fg">CGU</strong> (Controladoria-Geral da
            União) e <span className="text-alert">público</span>.
          </p>
          <p className="text-dim text-xs leading-relaxed">
            <strong className="text-fg">A regra:</strong> uma empresa
            sancionada NÃO pode receber contrato público novo. Na prática,
            órgãos federais frequentemente não consultam o CEIS antes de
            assinar — é exatamente isso que este sistema detecta.
          </p>

          <div className="grid md:grid-cols-3 gap-3 pt-2">
            {SANCOES.map((s) => (
              <div
                key={s.tipo}
                className={`border-l-4 ${s.barra} bg-bg/40 rounded-r p-3`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`inline-block px-2 py-0.5 border text-[10px] uppercase tracking-wider rounded ${s.cor}`}
                  >
                    {s.tipo}
                  </span>
                  <span className="text-dim text-[10px]">
                    {"●".repeat(s.gravidade)}
                    <span className="opacity-30">
                      {"●".repeat(4 - s.gravidade)}
                    </span>
                  </span>
                </div>
                <div className="text-fg text-xs font-medium mb-1.5">
                  {s.resumo}
                </div>
                <p className="text-dim text-xs leading-snug mb-2">
                  {s.descricao}
                </p>
                <div className="text-dim text-[10px] space-y-0.5 pt-2 border-t border-border">
                  <div>
                    <span className="text-dim/60">base legal:</span>{" "}
                    <span className="text-fg">{s.base_legal}</span>
                  </div>
                  <div>
                    <span className="text-dim/60">quem aplica:</span>{" "}
                    <span className="text-fg">{s.quem_aplica}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-border text-dim text-[11px] leading-relaxed">
            <strong className="text-fg">fontes:</strong>{" "}
            <a
              href="https://portaldatransparencia.gov.br/sancoes/ceis"
              target="_blank"
              rel="noreferrer"
              className="text-accent hover:underline"
            >
              portaltransparencia.gov.br/sancoes/ceis
            </a>{" "}
            · existem outros 3 cadastros parecidos (CNEP, CEPIM, Acordos de
            Leniência) que ainda não são ingeridos por este sistema.
          </div>
        </div>
      )}
    </div>
  );
}
