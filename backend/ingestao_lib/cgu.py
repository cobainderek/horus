"""Ingestão CEIS + contratos federais do Portal da Transparência (CGU).

Pipeline em duas camadas (bronze/silver):

    API CGU  ─→  data/raw/ceis_{data}.csv          (bronze: dado bruto)
                 data/raw/contratos_{data}.csv
                          │
                          └→  Postgres (silver: pronto pra cruzamento)

A camada bronze (CSV) permite reprocessar sem chamar a API de novo,
debug visual dos dados, e vira dataset pra análise descritiva.
"""
from __future__ import annotations

import csv
import os
import time
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from ..api.models import CEIS, ContratoPublico, Empresa

BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"
TIMEOUT = 30.0

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

COLUNAS_CEIS = [
    "cnpj", "razao_social", "tipo_sancao",
    "data_inicio_sancao", "data_fim_sancao", "orgao_sancionador",
    "fundamentacao", "numero_processo",
]
COLUNAS_CONTRATO = [
    "id", "cnpj_fornecedor", "razao_social", "orgao_contratante",
    "valor", "valor_inicial", "valor_final", "modalidade",
    "data_inicio", "data_fim", "data_assinatura", "numero_processo",
    "objeto",
]


class APIKeyError(RuntimeError):
    pass


def _headers() -> dict:
    chave = os.getenv("API_PORTAL_TRANSPARENCIA_KEY", "").strip()
    if not chave:
        raise APIKeyError(
            "API_PORTAL_TRANSPARENCIA_KEY não definida — cadastre em "
            "https://portaldatransparencia.gov.br/api-de-dados/cadastrar"
        )
    return {"chave-api-dados": chave, "Accept": "application/json"}


def _so_digitos(s: str) -> str:
    return "".join(c for c in (s or "") if c.isdigit())


def _data_br_iso(s: str | None) -> str | None:
    if not s or s.strip().lower() == "sem informação":
        return None
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def _hoje() -> str:
    return date.today().isoformat()


def _ensure_raw_dir() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def path_ceis_csv(data: str | None = None) -> Path:
    return RAW_DIR / f"ceis_{data or _hoje()}.csv"


def path_contratos_csv(data: str | None = None) -> Path:
    return RAW_DIR / f"contratos_{data or _hoje()}.csv"


# ─── HTTP ─────────────────────────────────────────────────────────────────

def buscar_ceis(client: httpx.Client, pagina: int) -> list[dict]:
    r = client.get(f"{BASE_URL}/ceis", headers=_headers(), params={"pagina": pagina})
    r.raise_for_status()
    return r.json()


def buscar_contratos(client: httpx.Client, cnpj: str, pagina: int = 1) -> list[dict]:
    r = client.get(
        f"{BASE_URL}/contratos/cpf-cnpj",
        headers=_headers(),
        params={"cpfCnpj": _so_digitos(cnpj), "pagina": pagina},
    )
    r.raise_for_status()
    return r.json()


# ─── PARSE ────────────────────────────────────────────────────────────────

def parse_ceis(item: dict) -> dict | None:
    pessoa = item.get("pessoa") or {}
    cnpj = (pessoa.get("cnpjFormatado") or "").strip()
    if not cnpj:
        return None
    razao = (
        pessoa.get("razaoSocialReceita")
        or pessoa.get("nome")
        or (item.get("sancionado") or {}).get("nome")
        or "(sem razão social)"
    ).strip()
    return {
        "cnpj": cnpj,
        "razao_social": razao[:300],
        "tipo_sancao": (item.get("tipoSancao") or {}).get("descricaoResumida", "")[:200],
        "data_inicio_sancao": _data_br_iso(item.get("dataInicioSancao")) or "",
        "data_fim_sancao": _data_br_iso(item.get("dataFimSancao")) or "",
        "orgao_sancionador": (item.get("orgaoSancionador") or {}).get("nome", "")[:200],
        "fundamentacao": (item.get("fundamentacao") or "")[:2000],
        "numero_processo": (item.get("numeroProcesso") or "")[:100],
    }


def parse_contrato(item: dict) -> dict | None:
    fornecedor = item.get("fornecedor") or {}
    cnpj = (fornecedor.get("cnpjFormatado") or "").strip()
    if not cnpj:
        return None
    unidade = item.get("unidadeGestora") or {}
    orgao_max = unidade.get("orgaoMaximo") or {}
    orgao_vinc = unidade.get("orgaoVinculado") or {}
    orgao_nome = (orgao_max.get("nome") or orgao_vinc.get("nome") or "").strip()
    valor_inicial = item.get("valorInicialCompra") or 0.0
    valor_final = item.get("valorFinalCompra") or 0.0
    # `valor` (legado) é sempre o valor final efetivo
    valor = valor_final or valor_inicial
    compra = item.get("compra") or {}
    return {
        "id": str(item.get("id") or "")[:20],
        "cnpj_fornecedor": cnpj,
        "razao_social": (
            fornecedor.get("razaoSocialReceita") or fornecedor.get("nome") or ""
        ).strip()[:300],
        "orgao_contratante": orgao_nome[:200] or "(sem informação)",
        "valor": str(float(valor)),
        "valor_inicial": str(float(valor_inicial)),
        "valor_final": str(float(valor_final)),
        "modalidade": (item.get("modalidadeCompra") or "")[:100],
        "data_inicio": (item.get("dataInicioVigencia") or "")[:10],
        "data_fim": (item.get("dataFimVigencia") or "")[:10],
        "data_assinatura": (item.get("dataAssinatura") or "")[:10],
        "numero_processo": (compra.get("numeroProcesso") or item.get("numeroProcesso") or "")[:100],
        "objeto": (item.get("objeto") or "")[:2000],
    }


# ─── BAIXAR (API → CSV) ───────────────────────────────────────────────────

def baixar_ceis_csv(max_paginas: int = 30, csv_path: Path | None = None) -> dict:
    """Baixa páginas do CEIS da API CGU e grava em CSV. Não toca no banco."""
    _ensure_raw_dir()
    out = csv_path or path_ceis_csv()
    n_linhas = pulados_pf = paginas_lidas = 0

    with open(out, "w", encoding="utf-8", newline="") as fh, httpx.Client(timeout=TIMEOUT) as client:
        w = csv.DictWriter(fh, fieldnames=COLUNAS_CEIS)
        w.writeheader()
        for pagina in range(1, max_paginas + 1):
            itens = buscar_ceis(client, pagina)
            if not itens:
                break
            paginas_lidas += 1
            for item in itens:
                p = parse_ceis(item)
                if p is None:
                    pulados_pf += 1
                    continue
                w.writerow(p)
                n_linhas += 1
            if pagina < max_paginas:
                time.sleep(0.5)

    return {"csv": str(out), "linhas": n_linhas, "pulados_pf": pulados_pf, "paginas_lidas": paginas_lidas}


def baixar_contratos_csv(
    cnpjs: Iterable[str],
    max_paginas_por_empresa: int = 2,
    csv_path: Path | None = None,
) -> dict:
    """Baixa contratos federais para os CNPJs dados e grava em CSV."""
    _ensure_raw_dir()
    out = csv_path or path_contratos_csv()
    cnpjs = list(cnpjs)
    n_linhas = empresas_com_contrato = erros = 0

    with open(out, "w", encoding="utf-8", newline="") as fh, httpx.Client(timeout=TIMEOUT) as client:
        w = csv.DictWriter(fh, fieldnames=COLUNAS_CONTRATO)
        w.writeheader()
        for i, cnpj in enumerate(cnpjs, 1):
            inseridos_emp = 0
            for pagina in range(1, max_paginas_por_empresa + 1):
                try:
                    itens = buscar_contratos(client, cnpj, pagina)
                except httpx.HTTPError as e:
                    erros += 1
                    print(f"    ! erro {cnpj} pag {pagina}: {type(e).__name__}")
                    break
                if not itens:
                    break
                for item in itens:
                    p = parse_contrato(item)
                    if p is None or not p["id"]:
                        continue
                    w.writerow(p)
                    n_linhas += 1
                    inseridos_emp += 1
                time.sleep(0.4)
            if inseridos_emp:
                empresas_com_contrato += 1
            if i % 20 == 0:
                print(f"    {i}/{len(cnpjs)} empresas consultadas (+{n_linhas} contratos)")

    return {
        "csv": str(out),
        "linhas": n_linhas,
        "empresas_consultadas": len(cnpjs),
        "empresas_com_contrato": empresas_com_contrato,
        "erros": erros,
    }


# ─── CARREGAR (CSV → BD) ──────────────────────────────────────────────────

def _upsert_empresa(db: Session, cnpj: str, razao: str) -> None:
    if db.query(Empresa).filter(Empresa.cnpj == cnpj).first() is None:
        db.add(Empresa(cnpj=cnpj, razao_social=razao or "(sem razão social)", situacao="ATIVA"))
        db.flush()


def carregar_ceis_csv(db: Session, csv_path: Path | None = None) -> dict:
    """Lê CSV de CEIS e faz upsert (insert OU update) no banco."""
    path = csv_path or path_ceis_csv()
    if not path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {path}")

    inseridos = atualizados = 0
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            inicio = row["data_inicio_sancao"] or None
            tipo = row["tipo_sancao"] or ""
            existente = db.query(CEIS).filter(
                CEIS.cnpj == row["cnpj"],
                CEIS.data_inicio_sancao == inicio,
                CEIS.tipo_sancao == tipo,
            ).first()
            extras = {
                "fundamentacao": row.get("fundamentacao") or None,
                "numero_processo": row.get("numero_processo") or None,
                "data_fim_sancao": row["data_fim_sancao"] or None,
                "orgao_sancionador": row["orgao_sancionador"],
            }
            if existente:
                for k, v in extras.items():
                    setattr(existente, k, v)
                atualizados += 1
            else:
                _upsert_empresa(db, row["cnpj"], row["razao_social"])
                db.add(CEIS(
                    cnpj=row["cnpj"],
                    razao_social=row["razao_social"],
                    tipo_sancao=tipo,
                    data_inicio_sancao=inicio,
                    **extras,
                ))
                inseridos += 1
    db.commit()
    return {"csv": str(path), "inseridos": inseridos, "atualizados": atualizados}


def carregar_contratos_csv(db: Session, csv_path: Path | None = None) -> dict:
    """Lê CSV de contratos e faz upsert (insert OU update) no banco."""
    path = csv_path or path_contratos_csv()
    if not path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {path}")

    inseridos = atualizados = 0
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if not row["id"]:
                continue
            dados = {
                "cnpj_fornecedor": row["cnpj_fornecedor"],
                "orgao_contratante": row["orgao_contratante"],
                "valor": float(row["valor"] or 0),
                "valor_inicial": float(row.get("valor_inicial") or 0) or None,
                "valor_final": float(row.get("valor_final") or 0) or None,
                "modalidade": row.get("modalidade") or None,
                "data_inicio": row["data_inicio"] or None,
                "data_fim": row["data_fim"] or None,
                "data_assinatura": row.get("data_assinatura") or None,
                "numero_processo": row.get("numero_processo") or None,
                "objeto": row["objeto"] or None,
            }
            existente = db.query(ContratoPublico).filter(
                ContratoPublico.id == row["id"]
            ).first()
            if existente:
                for k, v in dados.items():
                    setattr(existente, k, v)
                atualizados += 1
            else:
                _upsert_empresa(db, row["cnpj_fornecedor"], row["razao_social"])
                db.add(ContratoPublico(id=row["id"], **dados))
                inseridos += 1
    db.commit()
    return {"csv": str(path), "inseridos": inseridos, "atualizados": atualizados}


# ─── WRAPPERS DE COMPATIBILIDADE (usados pelo Celery e tasks legadas) ───

def ingerir_ceis(db: Session, max_paginas: int = 30) -> dict:
    """Baixa CEIS direto pra CSV e carrega no banco — em sequência."""
    r_bx = baixar_ceis_csv(max_paginas=max_paginas)
    r_ld = carregar_ceis_csv(db, Path(r_bx["csv"]))
    return {**r_bx, **r_ld}


def ingerir_contratos_sancionados(
    db: Session,
    max_empresas: int | None = None,
    max_paginas_por_empresa: int = 2,
) -> dict:
    """Pega CNPJs do CEIS no banco, baixa contratos em CSV, carrega no banco."""
    cnpjs = [
        c[0]
        for c in db.query(Empresa.cnpj)
        .join(CEIS, CEIS.cnpj == Empresa.cnpj)
        .distinct()
        .all()
    ]
    if max_empresas:
        cnpjs = cnpjs[:max_empresas]
    r_bx = baixar_contratos_csv(cnpjs, max_paginas_por_empresa=max_paginas_por_empresa)
    r_ld = carregar_contratos_csv(db, Path(r_bx["csv"]))
    return {**r_bx, **r_ld}
