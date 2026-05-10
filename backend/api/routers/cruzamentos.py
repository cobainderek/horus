"""Os 5 cruzamentos principais do Hórus."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...analytics.fuzzy_match import cruzar_agentes_socios_por_nome
from ..database import get_db
from ..schemas import ConflitoInteresse, EmpresaSancionadaContrato, RetornoFavor

router = APIRouter(prefix="/cruzamentos", tags=["Cruzamentos"])


@router.get("/conflito-interesse", response_model=list[ConflitoInteresse])
def conflito_interesse(
    valor_min: float = Query(0, description="valor mínimo do contrato"),
    db: Session = Depends(get_db),
):
    """Cruzamento 1 — político sócio de empresa contratada (match por CPF)."""
    rows = db.execute(text("""
        SELECT a.nome AS agente_nome, a.cpf AS agente_cpf, a.orgao AS agente_orgao,
               e.razao_social AS empresa_razao_social, e.cnpj AS empresa_cnpj,
               c.valor AS contrato_valor, c.objeto AS contrato_objeto,
               c.orgao_contratante, a.score_risco
          FROM agentes_publicos a
          JOIN socios_empresa s ON s.cpf_socio = a.cpf
          JOIN empresas e ON e.cnpj = s.cnpj_empresa
          JOIN contratos_publicos c ON c.cnpj_fornecedor = e.cnpj
         WHERE LOWER(c.orgao_contratante) LIKE '%' || LOWER(a.orgao) || '%'
           AND c.valor >= :v
         ORDER BY c.valor DESC
    """), {"v": valor_min}).fetchall()
    return [ConflitoInteresse(**dict(r._mapping)) for r in rows]


@router.get("/conflito-interesse-por-nome")
def conflito_por_nome(
    threshold: int = Query(90, ge=70, le=100),
    apenas_orgao_bate: bool = Query(False),
    limite: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Cruzamento 1 (versão fuzzy por nome) — driblando CPF mascarado por LGPD."""
    matches = cruzar_agentes_socios_por_nome(db, threshold=threshold)
    if apenas_orgao_bate:
        matches = [m for m in matches if m["orgao_bate"]]
    return matches[:limite]


@router.get("/retorno-favor", response_model=list[RetornoFavor])
def retorno_favor(db: Session = Depends(get_db)):
    """Cruzamento 2 — doador eleitoral → contrato federal."""
    rows = db.execute(text("""
        SELECT d.cnpj_doador AS doador_cnpj, d.nome_doador AS doador_nome,
               d.valor AS valor_doacao, d.ano_eleicao,
               d.nome_candidato AS candidato_nome,
               c.valor AS contrato_valor, c.orgao_contratante AS contrato_orgao,
               c.objeto AS contrato_objeto
          FROM doacoes_eleitorais d
          JOIN contratos_publicos c ON c.cnpj_fornecedor = d.cnpj_doador
         ORDER BY c.valor DESC
    """)).fetchall()
    return [RetornoFavor(**dict(r._mapping)) for r in rows]


@router.get("/empresa-sancionada", response_model=list[EmpresaSancionadaContrato])
def empresa_sancionada(db: Session = Depends(get_db)):
    """Cruzamento 5 — empresa no CEIS com contrato federal ativo."""
    rows = db.execute(text("""
        SELECT ce.cnpj, ce.razao_social, ce.tipo_sancao,
               c.valor AS contrato_valor,
               c.orgao_contratante AS contrato_orgao,
               c.objeto AS contrato_objeto
          FROM ceis ce
          JOIN contratos_publicos c ON c.cnpj_fornecedor = ce.cnpj
         ORDER BY c.valor DESC
    """)).fetchall()
    return [EmpresaSancionadaContrato(**dict(r._mapping)) for r in rows]


@router.get("/resumo")
def resumo(db: Session = Depends(get_db)):
    """Contagens consolidadas dos cruzamentos."""
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
        SELECT COUNT(*) FROM ceis ce
          JOIN contratos_publicos c ON c.cnpj_fornecedor = ce.cnpj
    """)).scalar() or 0
    return {
        "conflito_interesse": c1,
        "retorno_favor": c2,
        "empresa_sancionada": c5,
        "total": c1 + c2 + c5,
    }
