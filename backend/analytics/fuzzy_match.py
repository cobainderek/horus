"""Cruzamento 1 por similaridade de nome (CPFs vêm mascarados por LGPD)."""
from __future__ import annotations

import unicodedata

from rapidfuzz import fuzz, process
from sqlalchemy import text
from sqlalchemy.orm import Session


def _normalizar(s: str | None) -> str:
    if not s:
        return ""
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").upper().strip()


def cruzar_agentes_socios_por_nome(db: Session, threshold: int = 90) -> list[dict]:
    agentes = db.execute(text("""
        SELECT cpf, nome, orgao, cargo, remuneracao, score_risco
          FROM agentes_publicos
         WHERE nome IS NOT NULL AND length(trim(nome)) > 5
    """)).fetchall()

    socios = db.execute(text("""
        SELECT s.id AS socio_id, s.cpf_socio, s.nome_socio, s.qualificacao,
               e.cnpj AS empresa_cnpj, e.razao_social AS empresa_razao,
               COUNT(c.id) AS n_contratos,
               COALESCE(SUM(c.valor), 0) AS total_contratado,
               STRING_AGG(DISTINCT c.orgao_contratante, ' | ') AS orgaos_contratantes
          FROM socios_empresa s
          JOIN empresas e ON e.cnpj = s.cnpj_empresa
          LEFT JOIN contratos_publicos c ON c.cnpj_fornecedor = e.cnpj
         WHERE s.nome_socio IS NOT NULL AND length(trim(s.nome_socio)) > 5
         GROUP BY s.id, s.cpf_socio, s.nome_socio, s.qualificacao, e.cnpj, e.razao_social
        HAVING COUNT(c.id) > 0
    """)).fetchall()

    if not agentes or not socios:
        return []

    socios_norm = [_normalizar(s.nome_socio) for s in socios]
    matches: list[dict] = []

    for ag in agentes:
        nome_ag = _normalizar(ag.nome)
        if len(nome_ag) < 6:
            continue
        candidatos = process.extract(
            nome_ag, socios_norm,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=threshold,
            limit=5,
        )
        for _, score, idx in candidatos:
            s = socios[idx]
            orgao_bate = bool(
                ag.orgao and s.orgaos_contratantes
                and ag.orgao.strip().upper() in s.orgaos_contratantes.upper()
            )
            matches.append({
                "agente_nome": ag.nome,
                "agente_cpf": ag.cpf,
                "agente_orgao": ag.orgao,
                "agente_cargo": ag.cargo,
                "agente_remuneracao": float(ag.remuneracao or 0.0),
                "socio_nome": s.nome_socio,
                "socio_cpf": s.cpf_socio,
                "empresa_cnpj": s.empresa_cnpj,
                "empresa_razao_social": s.empresa_razao,
                "n_contratos": int(s.n_contratos),
                "total_contratado": float(s.total_contratado),
                "orgaos_contratantes": s.orgaos_contratantes,
                "similaridade_nome": round(float(score), 1),
                "orgao_bate": orgao_bate,
            })

    matches.sort(
        key=lambda m: (m["orgao_bate"], m["similaridade_nome"], m["total_contratado"]),
        reverse=True,
    )
    return matches
