// Cliente HTTP da API Hórus.
// SSR (server component): usa URL absoluta (Node fetch exige).
// Client (browser): usa /api → proxy do next.config.js → :8001.

const API_BASE_SERVER =
  process.env.HORUS_API_URL ?? "http://localhost:8001";
const API_BASE_CLIENT = "/api";

export async function apiGet<T>(path: string): Promise<T> {
  const base = typeof window === "undefined" ? API_BASE_SERVER : API_BASE_CLIENT;
  const r = await fetch(`${base}${path}`, { cache: "no-store" });
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

export type Caso = {
  empresa: {
    cnpj: string;
    razao_social: string;
    link_transparencia: string;
  };
  sancoes: Array<{
    tipo: string;
    orgao_sancionador: string;
    inicio: string | null;
    fim: string | null;
  }>;
  contratos: Array<{
    id: string;
    orgao: string;
    valor: number;
    objeto: string;
    data_inicio: string | null;
    data_fim: string | null;
  }>;
  valor_total: number;
  n_contratos: number;
};

export type GrafoD3 = {
  nodes: Array<{ id: string; kind: string; label: string; [k: string]: any }>;
  links: Array<{ source: string; target: string; kind: string; [k: string]: any }>;
};

export const fmtBRL = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 2 });

export const fmtNum = (v: number) => v.toLocaleString("pt-BR");
