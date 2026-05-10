import { GrafoForce } from "@/components/GrafoForce";

export const dynamic = "force-dynamic";

export default function GrafoPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-accent text-base">$ grafo — relacionamentos agente / empresa / órgão</h1>
        <p className="text-dim text-xs mt-1">
          arestas: SOCIO (agente→empresa) · CONTRATO (empresa→órgão) · DOOU (empresa→candidato).
          filtrado em contratos &gt; R$ 100k.
        </p>
        <div className="flex gap-4 text-xs mt-3 text-dim">
          <span><span className="inline-block w-3 h-3 rounded-full bg-accent mr-1.5 align-middle" />agente</span>
          <span><span className="inline-block w-3 h-3 rounded-full bg-alert mr-1.5 align-middle" />empresa</span>
          <span><span className="inline-block w-3 h-3 rounded-full mr-1.5 align-middle" style={{background:"#7ab0e0"}} />órgão</span>
        </div>
      </div>
      <GrafoForce />
    </div>
  );
}
