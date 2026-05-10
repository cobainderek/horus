"""Busca unificada por CPF ou CNPJ."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...analytics.score import calcular_score_agente, calcular_score_empresa
from ..database import get_db
from ..models import AgentePublico, CEIS, ContratoPublico, Empresa, SocioEmpresa
from ..schemas import Busca

router = APIRouter(prefix="/busca", tags=["Busca"])


def _so_digitos(s: str) -> str:
    return "".join(c for c in (s or "") if c.isdigit())


@router.get("/{ident}", response_model=Busca)
def buscar(ident: str, db: Session = Depends(get_db)):
    digitos = _so_digitos(ident)

    if len(digitos) == 11 or ident.count(".") >= 2:
        agente = db.query(AgentePublico).filter(AgentePublico.cpf == ident).first()
        if not agente:
            agente = (
                db.query(AgentePublico)
                .filter(AgentePublico.cpf.like(f"%{digitos[-6:]}%") if digitos else AgentePublico.cpf == ident)
                .first()
            )
        if agente:
            return _resp_agente(agente, db)

    empresa = db.query(Empresa).filter(Empresa.cnpj == ident).first()
    if empresa:
        return _resp_empresa(empresa, db)
    if len(digitos) == 14:
        empresa = (
            db.query(Empresa)
            .filter(Empresa.cnpj.like(f"%{digitos[-6:]}%"))
            .first()
        )
        if empresa:
            return _resp_empresa(empresa, db)

    raise HTTPException(status_code=404, detail=f"Nada encontrado para: {ident}")


def _resp_agente(a: AgentePublico, db: Session) -> Busca:
    score = calcular_score_agente(a.cpf, db)
    vinculos = db.query(SocioEmpresa).filter(SocioEmpresa.cpf_socio == a.cpf).all()
    irreg = []
    for v in vinculos:
        contratos = db.query(ContratoPublico).filter(
            ContratoPublico.cnpj_fornecedor == v.cnpj_empresa,
            ContratoPublico.orgao_contratante.ilike(f"%{a.orgao}%"),
        ).all()
        for c in contratos:
            irreg.append({
                "tipo": "Conflito de Interesse",
                "empresa": v.empresa.razao_social,
                "valor": c.valor,
                "orgao": c.orgao_contratante,
            })
        for s in db.query(CEIS).filter(CEIS.cnpj == v.cnpj_empresa).all():
            irreg.append({
                "tipo": "Empresa Sancionada (CEIS)",
                "empresa": s.razao_social,
                "sancao": s.tipo_sancao,
            })
    return Busca(
        tipo="agente",
        dados={
            "cpf": a.cpf, "nome": a.nome, "orgao": a.orgao,
            "cargo": a.cargo, "remuneracao": a.remuneracao,
            "vinculos_societarios": [
                {"empresa": v.empresa.razao_social, "cnpj": v.cnpj_empresa, "qualificacao": v.qualificacao}
                for v in vinculos
            ],
        },
        score_risco=score,
        irregularidades=irreg,
    )


def _resp_empresa(e: Empresa, db: Session) -> Busca:
    score = calcular_score_empresa(e.cnpj, db)
    contratos = db.query(ContratoPublico).filter(
        ContratoPublico.cnpj_fornecedor == e.cnpj
    ).all()
    sancoes = db.query(CEIS).filter(CEIS.cnpj == e.cnpj).all()
    socios = db.query(SocioEmpresa).filter(SocioEmpresa.cnpj_empresa == e.cnpj).all()

    irreg = []
    for s in sancoes:
        irreg.append({"tipo": "Empresa Sancionada (CEIS)", "sancao": s.tipo_sancao, "orgao_sancionador": s.orgao_sancionador})

    return Busca(
        tipo="empresa",
        dados={
            "cnpj": e.cnpj, "razao_social": e.razao_social,
            "situacao": e.situacao, "data_abertura": e.data_abertura,
            "socios": [{"nome": s.nome_socio, "cpf": s.cpf_socio, "qualificacao": s.qualificacao} for s in socios],
            "contratos": [{"orgao": c.orgao_contratante, "valor": c.valor, "objeto": c.objeto} for c in contratos],
        },
        score_risco=score,
        irregularidades=irreg,
    )
