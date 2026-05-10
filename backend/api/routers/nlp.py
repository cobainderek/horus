"""Endpoints de NLP sobre objetos de contrato (spaCy pt_core_news_lg)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...analytics.nlp import entidades_em_contratos, top_entidades
from ..database import get_db

router = APIRouter(prefix="/nlp", tags=["NLP"])


@router.get("/entidades-contratos")
def entidades(
    limite: int = Query(100, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """Extrai entidades nomeadas (PESSOA, ORG, LOC) dos objetos de contrato."""
    return entidades_em_contratos(db, limite=limite)


@router.get("/top-entidades")
def top(
    rotulo: str = Query("ORG", description="rótulo spaCy: PER, ORG, LOC, MISC"),
    limite: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Top entidades por co-menção em objetos de contrato."""
    return top_entidades(db, rotulo=rotulo, limite=limite)
