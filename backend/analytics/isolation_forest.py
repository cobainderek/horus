"""Detecção de anomalias em empresas via Isolation Forest (scikit-learn)."""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import text
from sqlalchemy.orm import Session

MODEL_PATH = Path(__file__).parent / "isolation_forest.joblib"


FEATURES = [
    "n_socios",
    "n_contratos",
    "valor_total",
    "valor_medio",
    "tem_ceis",
    "tem_doacao",
    "socio_servidor",
]


def _features_df(db: Session) -> pd.DataFrame:
    rows = db.execute(text("""
        SELECT
            e.cnpj,
            e.razao_social,
            COALESCE(COUNT(DISTINCT s.id), 0) AS n_socios,
            COALESCE(COUNT(DISTINCT c.id), 0) AS n_contratos,
            COALESCE(SUM(c.valor), 0) AS valor_total,
            CASE WHEN COUNT(DISTINCT c.id) > 0 THEN COALESCE(SUM(c.valor), 0) / COUNT(DISTINCT c.id) ELSE 0 END AS valor_medio,
            CASE WHEN EXISTS (SELECT 1 FROM ceis ce WHERE ce.cnpj = e.cnpj) THEN 1 ELSE 0 END AS tem_ceis,
            CASE WHEN EXISTS (SELECT 1 FROM doacoes_eleitorais d WHERE d.cnpj_doador = e.cnpj) THEN 1 ELSE 0 END AS tem_doacao,
            CASE WHEN EXISTS (
                SELECT 1 FROM socios_empresa ss
                  JOIN agentes_publicos a ON a.cpf = ss.cpf_socio
                 WHERE ss.cnpj_empresa = e.cnpj
            ) THEN 1 ELSE 0 END AS socio_servidor
          FROM empresas e
          LEFT JOIN socios_empresa s ON s.cnpj_empresa = e.cnpj
          LEFT JOIN contratos_publicos c ON c.cnpj_fornecedor = e.cnpj
         GROUP BY e.cnpj, e.razao_social
    """)).fetchall()
    return pd.DataFrame([dict(r._mapping) for r in rows])


def treinar_modelo(db: Session, contamination: float = 0.1, n_estimators: int = 200) -> dict:
    df = _features_df(db)
    if len(df) < 10:
        raise ValueError(f"Poucos dados para treinar ({len(df)} empresas). Mínimo: 10.")

    X = df[FEATURES].to_numpy()
    model = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=42,
    )
    model.fit(X)

    joblib.dump({"model": model, "features": FEATURES}, MODEL_PATH)
    return {
        "n_empresas": int(len(df)),
        "n_features": len(FEATURES),
        "contamination": contamination,
        "n_estimators": n_estimators,
        "modelo": str(MODEL_PATH),
    }


def prever_anomalias(db: Session, top_n: int = 20) -> list[dict]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("modelo não treinado — rode POST /ml/treinar primeiro")

    pkg = joblib.load(MODEL_PATH)
    model = pkg["model"]
    df = _features_df(db)
    if df.empty:
        return []

    X = df[FEATURES].to_numpy()
    scores = -model.score_samples(X)  # quanto maior, mais anômalo
    df["anomaly_score"] = scores

    top = df.nlargest(top_n, "anomaly_score")
    return [
        {
            "cnpj": r["cnpj"],
            "razao_social": r["razao_social"],
            "anomaly_score": round(float(r["anomaly_score"]), 4),
            "features": {f: float(r[f]) for f in FEATURES},
        }
        for _, r in top.iterrows()
    ]
