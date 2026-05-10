"""KPIs e métricas pro frontend."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AgentePublico, ContratoPublico, Empresa
from ..schemas import KPIs

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=KPIs)
def kpis(db: Session = Depends(get_db)):
    total_agentes = db.query(AgentePublico).count()
    total_empresas = db.query(Empresa).count()
    total_contratos = db.query(ContratoPublico).count()
    total_sancoes = db.execute(text("SELECT COUNT(*) FROM ceis")).scalar() or 0

    c1 = db.execute(text("""
        SELECT COUNT(*) FROM agentes_publicos a
          JOIN socios_empresa s ON s.cpf_socio = a.cpf
          JOIN contratos_publicos c ON c.cnpj_fornecedor = s.cnpj_empresa
         WHERE LOWER(c.orgao_contratante) LIKE '%' || LOWER(a.orgao) || '%'
    """)).scalar() or 0
    c2 = db.execute(text("""
        SELECT COUNT(*) FROM doacoes_eleitorais d
          JOIN contratos_publicos c ON c.cnpj_fornecedor = d.cnpj_doador
    """)).scalar() or 0
    c5 = db.execute(text("""
        SELECT COUNT(DISTINCT c.id) FROM contratos_publicos c
         WHERE EXISTS (SELECT 1 FROM ceis ce WHERE ce.cnpj = c.cnpj_fornecedor)
    """)).scalar() or 0

    valor_suspeito = db.execute(text("""
        SELECT COALESCE(SUM(valor), 0) FROM (
            SELECT DISTINCT c.id, c.valor FROM contratos_publicos c
              JOIN ceis ce ON ce.cnpj = c.cnpj_fornecedor
            UNION
            SELECT DISTINCT c.id, c.valor FROM contratos_publicos c
              JOIN socios_empresa s ON s.cnpj_empresa = c.cnpj_fornecedor
              JOIN agentes_publicos a ON a.cpf = s.cpf_socio
             WHERE LOWER(c.orgao_contratante) LIKE '%' || LOWER(a.orgao) || '%'
        ) t
    """)).scalar() or 0.0

    return KPIs(
        total_agentes=total_agentes,
        total_empresas=total_empresas,
        total_contratos=total_contratos,
        total_sancoes=int(total_sancoes),
        total_irregularidades=c1 + c2 + c5,
        valor_contratos_suspeitos=float(valor_suspeito),
    )


@router.get("/top-empresas")
def top_empresas(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT e.cnpj, e.razao_social,
               COUNT(DISTINCT c.id) AS n_contratos,
               COALESCE(SUM(c.valor), 0) AS valor_total,
               e.score_risco
          FROM empresas e
          JOIN ceis ce ON ce.cnpj = e.cnpj
          JOIN contratos_publicos c ON c.cnpj_fornecedor = e.cnpj
         GROUP BY e.cnpj, e.razao_social, e.score_risco
         ORDER BY valor_total DESC
         LIMIT :lim
    """), {"lim": limit}).fetchall()
    return [
        {
            "cnpj": r.cnpj,
            "razao_social": r.razao_social,
            "n_contratos": int(r.n_contratos),
            "valor_total": float(r.valor_total),
            "score_risco": float(r.score_risco or 0),
        }
        for r in rows
    ]


@router.get("/top-orgaos")
def top_orgaos(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT c.orgao_contratante AS orgao,
               COUNT(DISTINCT c.id) AS n_contratos,
               COALESCE(SUM(c.valor), 0) AS valor_total
          FROM contratos_publicos c
          JOIN ceis ce ON ce.cnpj = c.cnpj_fornecedor
         GROUP BY c.orgao_contratante
         ORDER BY valor_total DESC
         LIMIT :lim
    """), {"lim": limit}).fetchall()
    return [
        {
            "orgao": r.orgao,
            "n_contratos": int(r.n_contratos),
            "valor_total": float(r.valor_total),
        }
        for r in rows
    ]


@router.get("/distribuicao-sancoes")
def distribuicao_sancoes(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT tipo_sancao AS tipo, COUNT(*) AS quantidade
          FROM ceis
         WHERE tipo_sancao IS NOT NULL AND tipo_sancao != ''
         GROUP BY tipo_sancao
         ORDER BY quantidade DESC
    """)).fetchall()
    return [{"tipo": r.tipo, "quantidade": int(r.quantidade)} for r in rows]
