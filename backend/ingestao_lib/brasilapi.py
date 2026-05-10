"""Ingestão do QSA via BrasilAPI — para cada empresa do banco, busca sócios."""
from __future__ import annotations

import time

import httpx
from sqlalchemy.orm import Session

from ..api.models import Empresa, SocioEmpresa

BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"


def _so_digitos(s: str) -> str:
    return "".join(c for c in (s or "") if c.isdigit())


def buscar_qsa(client: httpx.Client, cnpj: str) -> dict | None:
    r = client.get(f"{BASE_URL}/{_so_digitos(cnpj)}")
    if r.status_code == 200:
        return r.json()
    return None


def ingerir_qsa(db: Session, max_empresas: int | None = None, sleep_segundos: float = 0.5) -> dict:
    cnpjs = [c[0] for c in db.query(Empresa.cnpj).distinct().all()]
    if max_empresas:
        cnpjs = cnpjs[:max_empresas]

    socios_inseridos = 0
    com_qsa = 0
    erros = 0
    with httpx.Client(timeout=30.0) as client:
        for cnpj in cnpjs:
            try:
                dados = buscar_qsa(client, cnpj)
            except httpx.HTTPError:
                erros += 1
                continue
            if not dados:
                erros += 1
                continue

            qsa = dados.get("qsa") or []
            if qsa:
                com_qsa += 1
            for i, s in enumerate(qsa):
                nome = (s.get("nome_socio") or "").strip()
                if not nome:
                    continue
                socio_id = f"{_so_digitos(cnpj)}-{i}"
                if db.query(SocioEmpresa).filter(SocioEmpresa.id == socio_id).first():
                    continue
                db.add(SocioEmpresa(
                    id=socio_id,
                    cnpj_empresa=cnpj,
                    cpf_socio=(s.get("cnpj_cpf_do_socio") or "")[:14],
                    nome_socio=nome[:200],
                    qualificacao=(s.get("qualificacao_socio") or "")[:100],
                ))
                socios_inseridos += 1
            time.sleep(sleep_segundos)

    db.commit()
    return {"consultadas": len(cnpjs), "com_qsa": com_qsa, "socios_inseridos": socios_inseridos, "erros": erros}
