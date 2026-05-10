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
  const [size, setSize] = useState({ w: 800, h: 600 });

  useEffect(() => {
    apiGet<GrafoD3>("/grafo/d3?valor_min_contrato=100000")
      .then(setData)
      .catch((e) => setErro(e.message ?? String(e)));
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setSize({ w: Math.max(400, width), h: Math.max(400, height) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

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

  return (
    <div
      ref={containerRef}
      className="bg-card border border-border rounded overflow-hidden"
      style={{ height: "70vh" }}
    >
      <ForceGraph2D
        graphData={data}
        width={size.w}
        height={size.h}
        nodeLabel={(n: any) => `${n.kind}: ${n.label}`}
        nodeColor={(n: any) => cor(n.kind)}
        nodeRelSize={4}
        linkColor={() => "#1f2a26"}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        backgroundColor="#0a0f0c"
      />
    </div>
  );
}
