"""NLP com spaCy sobre os objetos de contrato.

Carrega o modelo pt_core_news_lg uma vez (lazy), processa textos e extrai
entidades nomeadas (PER, ORG, LOC). Útil pra cruzamento por co-menção:
descobrir quais órgãos/pessoas aparecem em objetos contratuais.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.orm import Session


@lru_cache(maxsize=1)
def _carregar_modelo():
    import spacy  # noqa: WPS433 — import dentro pra adiar custo

    try:
        return spacy.load("pt_core_news_lg")
    except OSError as e:
        raise RuntimeError(
            "modelo spaCy 'pt_core_news_lg' não instalado. "
            "rode: python -m spacy download pt_core_news_lg"
        ) from e


def entidades_em_contratos(db: Session, limite: int = 100) -> list[dict]:
    nlp = _carregar_modelo()

    rows = db.execute(text("""
        SELECT id, cnpj_fornecedor, orgao_contratante, objeto, valor
          FROM contratos_publicos
         WHERE objeto IS NOT NULL AND length(objeto) > 20
         ORDER BY valor DESC NULLS LAST
         LIMIT :lim
    """), {"lim": limite}).fetchall()

    saida = []
    for r in rows:
        doc = nlp(r.objeto or "")
        ents = [{"texto": e.text, "rotulo": e.label_} for e in doc.ents]
        saida.append({
            "contrato_id": r.id,
            "cnpj_fornecedor": r.cnpj_fornecedor,
            "orgao": r.orgao_contratante,
            "valor": float(r.valor or 0),
            "objeto": (r.objeto or "")[:240],
            "entidades": ents,
        })
    return saida


def top_entidades(db: Session, rotulo: str = "ORG", limite: int = 20) -> list[dict]:
    """Conta entidades por rótulo (PER/ORG/LOC/MISC) em todos os objetos."""
    nlp = _carregar_modelo()

    rows = db.execute(text("""
        SELECT objeto FROM contratos_publicos
         WHERE objeto IS NOT NULL AND length(objeto) > 20
    """)).fetchall()

    contador: Counter = Counter()
    for r in rows:
        doc = nlp(r.objeto or "")
        for e in doc.ents:
            if e.label_ == rotulo:
                contador[e.text.strip()] += 1

    return [
        {"entidade": txt, "ocorrencias": n}
        for txt, n in contador.most_common(limite)
    ]
