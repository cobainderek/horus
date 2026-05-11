import { CasoCard } from "@/components/CasoCard";
import { GlossarioSancoes } from "@/components/GlossarioSancoes";
import { KPICard } from "@/components/KPICard";
import {
  apiGet,
  fmtBRL,
  fmtNum,
  type Caso,
  type KPIs,
} from "@/lib/api";

export const dynamic = "force-dynamic";

async function carregar() {
  try {
    const [kpis, casos] = await Promise.all([
      apiGet<KPIs>("/dashboard/kpis"),
      apiGet<Caso[]>("/cruzamentos/casos?limite=300"),
    ]);
    return { kpis, casos, erro: null as string | null };
  } catch (e: any) {
    return { kpis: null, casos: [], erro: e?.message ?? String(e) };
  }
}

export default async function Page() {
  const { kpis, casos, erro } = await carregar();

  if (erro || !kpis) {
    return (
      <div className="bg-card border border-alert rounded p-6">
        <p className="text-alert">! API indisponível: {erro}</p>
        <p className="text-dim text-xs mt-2">
          suba o backend:{" "}
          <code className="bg-bg px-2 py-0.5 rounded">uvicorn backend.api.main:app --port 8001 --reload</code>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-accent text-base mb-1">
          $ relatório de fiscalização
        </h1>
        <p className="text-dim text-xs mb-4">
          fonte: portal da transparência (cgu) + receita federal (brasilapi).
          investigamos {fmtNum(casos.length)} empresas no CEIS.
          em {casos.filter(c => c.classificacao !== "POTENCIAL").length} houve sobreposição temporal entre sanção e contrato — irregularidade comprovada.
          nas demais {casos.filter(c => c.classificacao === "POTENCIAL").length}, os contratos detectados são anteriores à sanção atual: <span className="text-accent">não há prova de irregularidade</span>, mas reportamos o fato pra transparência.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <KPICard label="empresas no CEIS" value={fmtNum(kpis.total_sancoes)} />
          <KPICard label="contratos detectados" value={fmtNum(kpis.total_contratos)} />
          <KPICard label="casos comprovados" value={fmtNum(casos.filter(c => c.classificacao !== "POTENCIAL").length)} alert />
          <KPICard label="dinheiro público suspeito" value={fmtBRL(kpis.valor_contratos_suspeitos)} alert />
        </div>
        <GlossarioSancoes />
      </section>

      {(() => {
        const comprovados = casos.filter(c => c.classificacao !== "POTENCIAL");
        const semProva = casos.filter(c => c.classificacao === "POTENCIAL");
        let n = 0;
        return (
          <>
            {comprovados.length > 0 && (
              <section className="space-y-4">
                <div className="border-l-4 border-l-red-500 pl-3 mb-2">
                  <h2 className="text-fg text-sm font-semibold">
                    🚨 sobreposição temporal comprovada — {comprovados.length} caso{comprovados.length !== 1 ? "s" : ""}
                  </h2>
                  <p className="text-dim text-xs mt-0.5">
                    sanção e contrato vigentes ao mesmo tempo. irregularidade evidente.
                  </p>
                </div>
                {comprovados.map(c => {
                  n++;
                  return <CasoCard key={c.empresa.cnpj} caso={c} indice={n} />;
                })}
              </section>
            )}

            {semProva.length > 0 && (
              <section className="space-y-4 pt-6">
                <div className="border-l-4 border-l-dim/40 pl-3 mb-2">
                  <h2 className="text-dim text-sm font-semibold">
                    📋 empresas no CEIS sem sobreposição comprovada — {semProva.length} caso{semProva.length !== 1 ? "s" : ""}
                  </h2>
                  <p className="text-dim text-xs mt-0.5">
                    investigadas pelo algoritmo. estão sancionadas, mas os contratos detectados são <strong>anteriores</strong> à sanção atual. não há prova de irregularidade temporal — listadas pra transparência do método.
                  </p>
                </div>
                {semProva.map(c => {
                  n++;
                  return <CasoCard key={c.empresa.cnpj} caso={c} indice={n} />;
                })}
              </section>
            )}

            {casos.length === 0 && (
              <div className="bg-card border border-border rounded p-6 text-dim text-sm">
                nenhum caso ainda — rode{" "}
                <code className="text-fg">python -m backend.ingestao tudo</code>
              </div>
            )}
          </>
        );
      })()}
    </div>
  );
}
