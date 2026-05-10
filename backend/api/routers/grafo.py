"""Endpoints do grafo de relacionamentos (NetworkX + Apache AGE)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...analytics.grafo import construir_grafo, grafo_para_d3, metricas_grafo
from ..database import get_db

router = APIRouter(prefix="/grafo", tags=["Grafo"])


@router.get("/d3")
def grafo_d3(
    valor_min_contrato: float = Query(0, description="filtrar arestas de contrato abaixo desse valor"),
    db: Session = Depends(get_db),
):
    """Retorna o grafo em formato compatível com React Force Graph (nodes + links)."""
    g = construir_grafo(db, valor_min_contrato=valor_min_contrato)
    return grafo_para_d3(g)


@router.get("/metricas")
def metricas(db: Session = Depends(get_db)):
    """Métricas globais do grafo: nós, arestas, componentes, top centralidade."""
    g = construir_grafo(db)
    return metricas_grafo(g)
