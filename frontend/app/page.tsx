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
      apiGet<Caso[]>("/cruzamentos/casos?limite=50"),
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
        <h1 className="text-accent text-base mb-1">$ casos detectados — empresas sancionadas que receberam dinheiro público</h1>
        <p className="text-dim text-xs mb-4">
          fonte: portal da transparência (cgu) · cruzamento entre cadastro de empresas inidôneas/suspensas (ceis) e contratos federais ativos
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <KPICard label="empresas sancionadas" value={fmtNum(kpis.total_sancoes)} />
          <KPICard label="contratos detectados" value={fmtNum(kpis.total_contratos)} />
          <KPICard label="casos irregulares" value={fmtNum(kpis.total_irregularidades)} alert />
          <KPICard label="dinheiro público suspeito" value={fmtBRL(kpis.valor_contratos_suspeitos)} alert />
        </div>
        <GlossarioSancoes />
      </section>

      {casos.length === 0 ? (
        <div className="bg-card border border-border rounded p-6 text-dim text-sm">
          nenhum caso ainda — rode <code className="text-fg">python -m backend.ingestao contratos</code>
        </div>
      ) : (
        <section className="space-y-4">
          {casos.map((c, i) => (
            <CasoCard key={c.empresa.cnpj} caso={c} indice={i + 1} />
          ))}
        </section>
      )}
    </div>
  );
}
