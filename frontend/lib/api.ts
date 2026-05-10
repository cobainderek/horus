// Cliente HTTP minimalista para a API Hórus (proxied via /api → :8000).

export const API_BASE = "/api";

export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`API ${path}: ${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

export type KPIs = {
  total_agentes: number;
  total_empresas: number;
  total_contratos: number;
  total_sancoes: number;
  total_irregularidades: number;
  valor_contratos_suspeitos: number;
};

export type TopEmpresa = {
  cnpj: string;
  razao_social: string;
  n_contratos: number;
  valor_total: number;
  score_risco: number;
};

export type TopOrgao = {
  orgao: string;
  n_contratos: number;
  valor_total: number;
};

export type DistribuicaoSancao = {
  tipo: string;
  quantidade: number;
};

export type GrafoD3 = {
  nodes: Array<{ id: string; kind: string; label: string; [k: string]: any }>;
  links: Array<{ source: string; target: string; kind: string; [k: string]: any }>;
};

export const fmtBRL = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 2 });

export const fmtNum = (v: number) => v.toLocaleString("pt-BR");
