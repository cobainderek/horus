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
      <div className="bg-card border border-alert p-6">
        <p className="text-alert">[ERRO] API indisponível: {erro}</p>
        <p className="text-dim text-xs mt-2">
          <span className="text-accent">$</span> suba o backend:{" "}
          <code className="bg-bg px-2 py-0.5 text-fg">
            uvicorn backend.api.main:app --port 8001 --reload
          </code>
        </p>
      </div>
    );
  }

  const comprovados = casos.filter((c) => c.classificacao !== "POTENCIAL");
  const semProva = casos.filter((c) => c.classificacao === "POTENCIAL");

  return (
    <div className="space-y-8">
      {/* CABEÇALHO DO RELATÓRIO */}
      <section>
        <div className="text-accent text-xs mb-2 font-bold tracking-wider">
          ╔═══════════════════════════════════════════════════════════════════════════╗
        </div>
        <div className="text-accent text-base mb-1 flex items-center gap-2">
          <span>║</span>
          <span className="text-fg">$ relatório de fiscalização</span>
          <span className="ml-auto text-dim text-xs">[ {new Date().toLocaleDateString("pt-BR")} ]</span>
          <span>║</span>
        </div>
        <div className="text-accent text-xs mb-4 font-bold tracking-wider">
          ╚═══════════════════════════════════════════════════════════════════════════╝
        </div>

        <div className="bg-card border border-border p-4 mb-4 text-dim text-xs leading-relaxed">
          <div className="text-accent mb-2">{">"} método</div>
          <p>
            cruzamento entre <span className="text-fg">CEIS</span> (cadastro de empresas inidôneas/suspensas — CGU)
            e <span className="text-fg">contratos federais</span> (portal da transparência), enriquecido com
            dados cadastrais da <span className="text-fg">Receita Federal</span> (BrasilAPI).
          </p>
          <div className="text-accent mt-3 mb-2">{">"} achados</div>
          <p>
            investigamos <span className="text-accent font-bold">{fmtNum(casos.length)}</span> empresas no CEIS.
            em <span className="text-alert font-bold">{fmtNum(comprovados.length)}</span> há sobreposição temporal
            entre sanção e contrato — irregularidade comprovada matematicamente. nas demais
            <span className="text-fg"> {fmtNum(semProva.length)}</span> os contratos detectados são anteriores à
            sanção atual: <span className="text-accent">não há prova de irregularidade</span>, mas reportamos pra
            transparência do método.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <KPICard label="empresas no CEIS" value={fmtNum(kpis.total_sancoes)} />
          <KPICard label="contratos detectados" value={fmtNum(kpis.total_contratos)} />
          <KPICard label="casos comprovados" value={fmtNum(comprovados.length)} alert />
          <KPICard label="dinheiro público suspeito" value={fmtBRL(kpis.valor_contratos_suspeitos)} alert />
        </div>

        <GlossarioSancoes />
      </section>

      {/* SEÇÃO COMPROVADOS */}
      {comprovados.length > 0 && (
        <section className="space-y-4">
          <div className="border-l-4 border-l-red-500 pl-4 py-2 bg-red-950/20">
            <h2 className="text-fg text-sm font-bold flex items-center gap-2">
              <span className="text-red-400">[!]</span>
              sobreposição temporal comprovada
              <span className="text-dim font-normal">
                — {comprovados.length} caso{comprovados.length !== 1 ? "s" : ""}
              </span>
            </h2>
            <p className="text-dim text-xs mt-1">
              <span className="text-accent">{">"}</span> sanção e contrato vigentes simultaneamente. irregularidade evidente.
            </p>
          </div>
          {comprovados.map((c, i) => (
            <CasoCard key={c.empresa.cnpj} caso={c} indice={i + 1} />
          ))}
        </section>
      )}

      {/* SEÇÃO SEM PROVA */}
      {semProva.length > 0 && (
        <section className="space-y-4 pt-6">
          <div className="border-l-4 border-l-dim/40 pl-4 py-2 bg-card/40">
            <h2 className="text-dim text-sm font-bold flex items-center gap-2">
              <span className="text-dim">[?]</span>
              empresas no CEIS sem sobreposição comprovada
              <span className="text-dim font-normal">
                — {semProva.length} caso{semProva.length !== 1 ? "s" : ""}
              </span>
            </h2>
            <p className="text-dim text-xs mt-1">
              <span className="text-accent">{">"}</span> investigadas pelo algoritmo. estão sancionadas, mas os contratos
              detectados são <strong className="text-fg">anteriores</strong> à sanção atual. não há prova de
              irregularidade temporal — listadas pra transparência do método.
            </p>
          </div>
          {semProva.map((c, i) => (
            <CasoCard key={c.empresa.cnpj} caso={c} indice={comprovados.length + i + 1} />
          ))}
        </section>
      )}

      {casos.length === 0 && (
        <div className="bg-card border border-border p-6 text-dim text-sm">
          <span className="text-accent">$</span> nenhum caso ainda — rode{" "}
          <code className="text-fg">python -m backend.ingestao tudo</code>
        </div>
      )}
    </div>
  );
}
