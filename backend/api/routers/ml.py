"""Endpoints do Isolation Forest."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...analytics.isolation_forest import prever_anomalias, treinar_modelo
from ..database import get_db

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.post("/treinar")
def treinar(
    contamination: float = Query(0.1, gt=0.0, lt=0.5),
    n_estimators: int = Query(200, ge=50, le=1000),
    db: Session = Depends(get_db),
):
    try:
        return treinar_modelo(db, contamination=contamination, n_estimators=n_estimators)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/anomalias")
def listar(top_n: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    try:
        return prever_anomalias(db, top_n=top_n)
    except FileNotFoundError as e:
        raise HTTPException(status_code=409, detail=str(e))
