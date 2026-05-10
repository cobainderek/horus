"""Ingestão de CEIS + contratos federais do Portal da Transparência (CGU)."""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from ..api.models import CEIS, ContratoPublico, Empresa

BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"
TIMEOUT = 30.0


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
        "data_inicio_sancao": _data_br_iso(item.get("dataInicioSancao")),
        "data_fim_sancao": _data_br_iso(item.get("dataFimSancao")),
        "orgao_sancionador": (item.get("orgaoSancionador") or {}).get("nome", "")[:200],
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
    valor = item.get("valorFinalCompra") or item.get("valorInicialCompra") or 0.0
    return {
        "id": str(item.get("id") or "")[:20],
        "cnpj_fornecedor": cnpj,
        "orgao_contratante": orgao_nome[:200] or "(sem informação)",
        "valor": float(valor),
        "data_inicio": (item.get("dataInicioVigencia") or "")[:10] or None,
        "data_fim": (item.get("dataFimVigencia") or "")[:10] or None,
        "objeto": (item.get("objeto") or "")[:2000],
        "_razao_social": (
            fornecedor.get("razaoSocialReceita") or fornecedor.get("nome") or ""
        ).strip()[:300],
    }


# ─── PERSISTÊNCIA ────────────────────────────────────────────────────────

def _upsert_empresa(db: Session, cnpj: str, razao: str) -> None:
    if db.query(Empresa).filter(Empresa.cnpj == cnpj).first() is None:
        db.add(Empresa(cnpj=cnpj, razao_social=razao, situacao="ATIVA"))
        db.flush()


def ingerir_ceis(db: Session, max_paginas: int = 30) -> dict:
    inseridos = duplicados = pulados = 0
    with httpx.Client(timeout=TIMEOUT) as client:
        for pagina in range(1, max_paginas + 1):
            itens = buscar_ceis(client, pagina)
            if not itens:
                break
            for item in itens:
                p = parse_ceis(item)
                if p is None:
                    pulados += 1
                    continue
                ja = db.query(CEIS).filter(
                    CEIS.cnpj == p["cnpj"],
                    CEIS.data_inicio_sancao == p["data_inicio_sancao"],
                    CEIS.tipo_sancao == p["tipo_sancao"],
                ).first()
                if ja:
                    duplicados += 1
                    continue
                _upsert_empresa(db, p["cnpj"], p["razao_social"])
                db.add(CEIS(**p))
                inseridos += 1
            if pagina < max_paginas:
                time.sleep(0.5)
    db.commit()
    return {"inseridos": inseridos, "duplicados": duplicados, "pulados_pf": pulados}


def ingerir_contratos_sancionados(
    db: Session,
    max_empresas: int | None = None,
    max_paginas_por_empresa: int = 2,
) -> dict:
    cnpjs = [
        c[0]
        for c in db.query(Empresa.cnpj)
        .join(CEIS, CEIS.cnpj == Empresa.cnpj)
        .distinct()
        .all()
    ]
    if max_empresas:
        cnpjs = cnpjs[:max_empresas]

    totais = {"inseridos": 0, "duplicados": 0, "ignorados": 0, "erros": 0, "empresas_com_contrato": 0}
    with httpx.Client(timeout=TIMEOUT) as client:
        for cnpj in cnpjs:
            inseridos_emp = 0
            for pagina in range(1, max_paginas_por_empresa + 1):
                try:
                    itens = buscar_contratos(client, cnpj, pagina)
                except httpx.HTTPError:
                    totais["erros"] += 1
                    break
                if not itens:
                    break
                for item in itens:
                    p = parse_contrato(item)
                    if p is None or not p["id"]:
                        totais["ignorados"] += 1
                        continue
                    if db.query(ContratoPublico).filter(ContratoPublico.id == p["id"]).first():
                        totais["duplicados"] += 1
                        continue
                    razao = p.pop("_razao_social") or "(sem razão social)"
                    _upsert_empresa(db, p["cnpj_fornecedor"], razao)
                    db.add(ContratoPublico(**p))
                    totais["inseridos"] += 1
                    inseridos_emp += 1
                time.sleep(0.4)
            if inseridos_emp:
                totais["empresas_com_contrato"] += 1
    db.commit()
    return totais
