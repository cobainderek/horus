"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

import { apiGet, type GrafoD3 } from "@/lib/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const cor = (kind: string) =>
  ({ agente: "#6ee07a", empresa: "#e07a6e", orgao: "#7ab0e0" }[kind] || "#888");

export function GrafoForce() {
  const [data, setData] = useState<GrafoD3 | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });

  useEffect(() => {
    apiGet<GrafoD3>("/grafo/d3?valor_min_contrato=100000")
      .then(setData)
      .catch((e) => setErro(e.message ?? String(e)));
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const measure = () => {
      const r = el.getBoundingClientRect();
      setSize({ w: Math.max(400, Math.floor(r.width)), h: Math.max(400, Math.floor(r.height)) });
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [data]);

  if (erro) {
    return (
      <div className="bg-card border border-alert rounded p-6 text-alert">
        ! falha ao carregar grafo: {erro}
      </div>
    );
  }
  if (!data) {
    return <div className="text-dim text-sm">carregando grafo...</div>;
  }

  const empresas = data.nodes.filter((n) => n.kind === "empresa").length;
  const orgaos = data.nodes.filter((n) => n.kind === "orgao").length;
  const agentes = data.nodes.filter((n) => n.kind === "agente").length;

  return (
    <>
      <div className="text-dim text-xs mb-2">
        nós: {data.nodes.length} ({empresas} empresas · {orgaos} órgãos · {agentes} agentes)
        &middot; arestas: {data.links.length}
      </div>
      <div
        ref={containerRef}
        className="bg-card border border-border rounded overflow-hidden w-full"
        style={{ height: "70vh" }}
      >
        {size.w > 0 && (
          <ForceGraph2D
            ref={graphRef}
            graphData={data}
            width={size.w}
            height={size.h}
            nodeLabel={(n: any) => `${n.kind}: ${n.label}`}
            nodeColor={(n: any) => cor(n.kind)}
            nodeRelSize={5}
            nodeCanvasObject={(node: any, ctx: any, scale: number) => {
              const r = 5;
              ctx.beginPath();
              ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
              ctx.fillStyle = cor(node.kind);
              ctx.fill();
              if (scale > 1.2 && node.label) {
                const label =
                  node.label.length > 28 ? node.label.slice(0, 25) + "..." : node.label;
                ctx.font = `${Math.max(2, 10 / scale)}px JetBrains Mono, monospace`;
                ctx.fillStyle = "#d4e0d4";
                ctx.textAlign = "center";
                ctx.fillText(label, node.x, node.y + 12);
              }
            }}
            linkColor={() => "#6ee07a"}
            linkWidth={(l: any) => Math.min(6, Math.log10((l.valor_total ?? 1e5) / 1e5 + 1) * 2 + 0.5)}
            linkDirectionalArrowLength={5}
            linkDirectionalArrowRelPos={0.95}
            linkDirectionalArrowColor={() => "#6ee07a"}
            cooldownTime={3000}
            onEngineStop={() => graphRef.current?.zoomToFit(400, 60)}
            backgroundColor="#0a0f0c"
          />
        )}
      </div>
    </>
  );
}
