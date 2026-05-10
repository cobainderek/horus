import { KPICard } from "@/components/KPICard";
import { TopEmpresasChart } from "@/components/TopEmpresasChart";
import { DistribuicaoSancoes } from "@/components/DistribuicaoSancoes";
import {
  apiGet,
  fmtBRL,
  fmtNum,
  type DistribuicaoSancao,
  type KPIs,
  type TopEmpresa,
  type TopOrgao,
} from "@/lib/api";

export const dynamic = "force-dynamic";

async function carregar() {
  try {
    const [kpis, empresas, orgaos, sancoes] = await Promise.all([
      apiGet<KPIs>("/dashboard/kpis"),
      apiGet<TopEmpresa[]>("/dashboard/top-empresas?limit=10"),
      apiGet<TopOrgao[]>("/dashboard/top-orgaos?limit=10"),
      apiGet<DistribuicaoSancao[]>("/dashboard/distribuicao-sancoes"),
    ]);
    return { kpis, empresas, orgaos, sancoes, erro: null as string | null };
  } catch (e: any) {
    return { kpis: null, empresas: [], orgaos: [], sancoes: [], erro: e?.message ?? String(e) };
  }
}

export default async function Page() {
  const { kpis, empresas, orgaos, sancoes, erro } = await carregar();

  if (erro || !kpis) {
    return (
      <div className="bg-card border border-alert rounded p-6">
        <p className="text-alert">! API indisponível: {erro}</p>
        <p className="text-dim text-xs mt-2">
          suba o backend: <code className="bg-bg px-2 py-0.5 rounded">uvicorn backend.api.main:app --reload</code>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <section>
        <h1 className="text-accent text-base mb-3">
          $ dashboard — visão geral
        </h1>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <KPICard label="agentes monitorados" value={fmtNum(kpis.total_agentes)} />
          <KPICard label="empresas" value={fmtNum(kpis.total_empresas)} />
          <KPICard label="contratos" value={fmtNum(kpis.total_contratos)} />
          <KPICard label="sanções (ceis)" value={fmtNum(kpis.total_sancoes)} />
          <KPICard label="irregularidades" value={fmtNum(kpis.total_irregularidades)} alert />
          <KPICard label="contratos suspeitos" value={fmtBRL(kpis.valor_contratos_suspeitos)} alert />
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-5">
        <TopEmpresasChart data={empresas} />
        <DistribuicaoSancoes data={sancoes} />
      </section>

      <section className="bg-card border border-border rounded p-4">
        <h2 className="text-accent text-xs uppercase tracking-wider mb-3">
          $ top órgãos — que mais contrataram sancionadas
        </h2>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-dim uppercase text-[10px] tracking-wider">
              <th className="text-left py-2">órgão</th>
              <th className="text-right py-2">contratos</th>
              <th className="text-right py-2">valor total</th>
            </tr>
          </thead>
          <tbody>
            {orgaos.map((o) => (
              <tr key={o.orgao} className="border-t border-border hover:bg-bg">
                <td className="py-2">{o.orgao}</td>
                <td className="py-2 text-right">{o.n_contratos}</td>
                <td className="py-2 text-right text-alert">{fmtBRL(o.valor_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
