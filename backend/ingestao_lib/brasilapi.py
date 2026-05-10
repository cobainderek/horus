"""Ingestão BrasilAPI — dados cadastrais da Receita Federal + QSA.

Pipeline em duas camadas:

    BrasilAPI  ─→  data/raw/empresas_brasilapi_{data}.csv  (dados da empresa)
                   data/raw/socios_{data}.csv              (1 sócio por linha)
                          │
                          └→  Postgres (dados_cadastrais + socios_empresa)

Endpoint público https://brasilapi.com.br/api/cnpj/v1/{cnpj}.
Sem chave; rate-limit dinâmico — usa pausa entre requests.
"""
from __future__ import annotations

import csv
import time
from datetime import date
from pathlib import Path
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from ..api.models import DadosCadastrais, SocioEmpresa
from .cgu import RAW_DIR, _ensure_raw_dir, _so_digitos

BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"
TIMEOUT = 30.0


COLUNAS_EMPRESAS = [
    "cnpj", "nome_fantasia", "situacao_cadastral", "data_inicio_atividade",
    "capital_social", "porte", "natureza_juridica",
    "cnae_codigo", "cnae_descricao",
    "logradouro", "numero", "municipio", "uf",
    "telefone", "email", "opcao_simples",
]
COLUNAS_SOCIOS = [
    "cnpj_empresa", "ordem", "nome_socio", "cpf_socio", "qualificacao",
]


def path_empresas_csv(data: str | None = None) -> Path:
    return RAW_DIR / f"empresas_brasilapi_{data or date.today().isoformat()}.csv"


def path_socios_csv(data: str | None = None) -> Path:
    return RAW_DIR / f"socios_{data or date.today().isoformat()}.csv"


# ─── HTTP ─────────────────────────────────────────────────────────────────

def buscar_cnpj(client: httpx.Client, cnpj: str) -> dict | None:
    r = client.get(f"{BASE_URL}/{_so_digitos(cnpj)}")
    if r.status_code == 200:
        return r.json()
    return None


def parse_empresa(d: dict, cnpj_formatado: str) -> dict:
    """Extrai dados cadastrais do retorno BrasilAPI."""
    return {
        "cnpj": cnpj_formatado,
        "nome_fantasia": (d.get("nome_fantasia") or "")[:300],
        "situacao_cadastral": (d.get("descricao_situacao_cadastral") or "")[:50],
        "data_inicio_atividade": (d.get("data_inicio_atividade") or "")[:10],
        "capital_social": str(d.get("capital_social") or 0),
        "porte": (d.get("porte") or "")[:100],
        "natureza_juridica": (d.get("natureza_juridica") or "")[:200],
        "cnae_codigo": str(d.get("cnae_fiscal") or "")[:20],
        "cnae_descricao": (d.get("cnae_fiscal_descricao") or "")[:300],
        "logradouro": (d.get("logradouro") or "")[:200],
        "numero": (d.get("numero") or "")[:20],
        "municipio": (d.get("municipio") or "")[:100],
        "uf": (d.get("uf") or "")[:2],
        "telefone": (d.get("ddd_telefone_1") or "")[:50],
        "email": (d.get("email") or "")[:200],
        "opcao_simples": "1" if d.get("opcao_pelo_simples") else "0",
    }


def parse_socios(d: dict, cnpj_formatado: str) -> list[dict]:
    out = []
    for i, s in enumerate(d.get("qsa") or []):
        nome = (s.get("nome_socio") or "").strip()
        if not nome:
            continue
        out.append({
            "cnpj_empresa": cnpj_formatado,
            "ordem": str(i),
            "nome_socio": nome[:200],
            "cpf_socio": (s.get("cnpj_cpf_do_socio") or "")[:14],
            "qualificacao": (s.get("qualificacao_socio") or "")[:100],
        })
    return out


# ─── BAIXAR (API → CSV) ───────────────────────────────────────────────────

def baixar_empresas_csv(
    cnpjs: Iterable[str],
    sleep_segundos: float = 0.5,
    empresas_csv: Path | None = None,
    socios_csv: Path | None = None,
) -> dict:
    """Pra cada CNPJ, baixa BrasilAPI e grava 2 CSVs: empresas + sócios."""
    _ensure_raw_dir()
    p_emp = empresas_csv or path_empresas_csv()
    p_soc = socios_csv or path_socios_csv()
    cnpjs = list(cnpjs)
    consultadas = encontradas = erros = total_socios = 0

    with (
        open(p_emp, "w", encoding="utf-8", newline="") as fh_emp,
        open(p_soc, "w", encoding="utf-8", newline="") as fh_soc,
        httpx.Client(timeout=TIMEOUT) as client,
    ):
        w_emp = csv.DictWriter(fh_emp, fieldnames=COLUNAS_EMPRESAS)
        w_emp.writeheader()
        w_soc = csv.DictWriter(fh_soc, fieldnames=COLUNAS_SOCIOS)
        w_soc.writeheader()

        for i, cnpj in enumerate(cnpjs, 1):
            consultadas += 1
            try:
                dados = buscar_cnpj(client, cnpj)
            except httpx.HTTPError as e:
                erros += 1
                print(f"    ! erro {cnpj}: {type(e).__name__}")
                continue
            if not dados:
                erros += 1
                continue

            w_emp.writerow(parse_empresa(dados, cnpj))
            encontradas += 1

            socios = parse_socios(dados, cnpj)
            for s in socios:
                w_soc.writerow(s)
            total_socios += len(socios)

            if i % 20 == 0:
                print(f"    {i}/{len(cnpjs)} CNPJs consultados (+{encontradas} ok, +{total_socios} sócios, {erros} erros)")
            time.sleep(sleep_segundos)

    return {
        "csv_empresas": str(p_emp),
        "csv_socios": str(p_soc),
        "consultadas": consultadas,
        "encontradas": encontradas,
        "erros": erros,
        "socios": total_socios,
    }


# ─── CARREGAR (CSV → BD) ──────────────────────────────────────────────────

def carregar_empresas_csv(db: Session, csv_path: Path | None = None) -> dict:
    """Lê CSV de empresas (BrasilAPI) e popula tabela dados_cadastrais."""
    path = csv_path or path_empresas_csv()
    if not path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {path}")

    hoje = date.today().isoformat()
    inseridos = atualizados = 0
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            existente = db.query(DadosCadastrais).filter(
                DadosCadastrais.cnpj == row["cnpj"]
            ).first()
            dados = {
                "nome_fantasia": row["nome_fantasia"] or None,
                "situacao_cadastral": row["situacao_cadastral"] or None,
                "data_inicio_atividade": row["data_inicio_atividade"] or None,
                "capital_social": float(row["capital_social"] or 0) or None,
                "porte": row["porte"] or None,
                "natureza_juridica": row["natureza_juridica"] or None,
                "cnae_codigo": row["cnae_codigo"] or None,
                "cnae_descricao": row["cnae_descricao"] or None,
                "logradouro": row["logradouro"] or None,
                "numero": row["numero"] or None,
                "municipio": row["municipio"] or None,
                "uf": row["uf"] or None,
                "telefone": row["telefone"] or None,
                "email": row["email"] or None,
                "opcao_simples": 1 if row["opcao_simples"] == "1" else 0,
                "atualizado_em": hoje,
            }
            if existente:
                for k, v in dados.items():
                    setattr(existente, k, v)
                atualizados += 1
            else:
                db.add(DadosCadastrais(cnpj=row["cnpj"], **dados))
                inseridos += 1
    db.commit()
    return {"csv": str(path), "inseridos": inseridos, "atualizados": atualizados}


def carregar_socios_csv(db: Session, csv_path: Path | None = None) -> dict:
    """Lê CSV de sócios e popula tabela socios_empresa."""
    path = csv_path or path_socios_csv()
    if not path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {path}")

    inseridos = duplicados = 0
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            socio_id = f"{_so_digitos(row['cnpj_empresa'])}-{row['ordem']}"
            if db.query(SocioEmpresa).filter(SocioEmpresa.id == socio_id).first():
                duplicados += 1
                continue
            db.add(SocioEmpresa(
                id=socio_id,
                cnpj_empresa=row["cnpj_empresa"],
                cpf_socio=row["cpf_socio"][:14],
                nome_socio=row["nome_socio"],
                qualificacao=row["qualificacao"] or None,
            ))
            inseridos += 1
    db.commit()
    return {"csv": str(path), "inseridos": inseridos, "duplicados": duplicados}


# ─── COMPATIBILIDADE (Celery legado) ──────────────────────────────────────

def ingerir_qsa(db: Session, max_empresas: int | None = None, sleep_segundos: float = 0.5) -> dict:
    from ..api.models import Empresa
    cnpjs = [c[0] for c in db.query(Empresa.cnpj).distinct().all()]
    if max_empresas:
        cnpjs = cnpjs[:max_empresas]
    r_bx = baixar_empresas_csv(cnpjs, sleep_segundos=sleep_segundos)
    r_emp = carregar_empresas_csv(db, Path(r_bx["csv_empresas"]))
    r_soc = carregar_socios_csv(db, Path(r_bx["csv_socios"]))
    return {**r_bx, "carga_empresas": r_emp, "carga_socios": r_soc}
