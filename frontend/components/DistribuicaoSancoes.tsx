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

import type { DistribuicaoSancao } from "@/lib/api";

export function DistribuicaoSancoes({ data }: { data: DistribuicaoSancao[] }) {
  return (
    <div className="bg-card border border-border rounded p-4">
      <h2 className="text-accent text-xs uppercase tracking-wider mb-3">
        $ distribuição — tipos de sanção
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid stroke="#1f2a26" />
          <XAxis dataKey="tipo" stroke="#6f8a73" tick={{ fontSize: 9 }} angle={-25} textAnchor="end" height={70} />
          <YAxis stroke="#6f8a73" />
          <Tooltip contentStyle={{ background: "#11181a", border: "1px solid #1f2a26" }} />
          <Bar dataKey="quantidade" fill="#6ee07a" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
