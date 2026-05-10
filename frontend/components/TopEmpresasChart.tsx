"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TopEmpresa } from "@/lib/api";
import { fmtBRL } from "@/lib/api";

export function TopEmpresasChart({ data }: { data: TopEmpresa[] }) {
  const chartData = data.map((e) => ({
    nome: e.razao_social.length > 30 ? e.razao_social.slice(0, 27) + "..." : e.razao_social,
    valor: e.valor_total,
    cnpj: e.cnpj,
  }));

  return (
    <div className="bg-card border border-border rounded p-4">
      <h2 className="text-accent text-xs uppercase tracking-wider mb-3">
        $ top empresas — valor total contratado
      </h2>
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 80 }}>
          <CartesianGrid stroke="#1f2a26" />
          <XAxis
            type="number"
            stroke="#6f8a73"
            tickFormatter={(v) => `R$ ${(v / 1e6).toFixed(0)}M`}
          />
          <YAxis
            type="category"
            dataKey="nome"
            stroke="#6f8a73"
            width={200}
            tick={{ fontSize: 10 }}
          />
          <Tooltip
            contentStyle={{ background: "#11181a", border: "1px solid #1f2a26" }}
            formatter={(v: number) => fmtBRL(v)}
          />
          <Bar dataKey="valor" fill="#e07a6e" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
