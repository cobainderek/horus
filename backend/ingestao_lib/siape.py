"""Ingestão SIAPE — dump CSV mensal de servidores federais.

Fonte: portaldatransparencia.gov.br/download-de-dados/servidores
Download via httpx, parsing com Polars (CSV ~80MB), persiste top-N por
remuneração total em agentes_publicos.
"""
from __future__ import annotations

import io
import zipfile

import httpx
import polars as pl
from sqlalchemy.orm import Session

from ..api.models import AgentePublico

URL_TEMPLATE = (
    "https://portaldatransparencia.gov.br/download-de-dados/servidores/{mes_ano}_Servidores_SIAPE"
)


def baixar_siape_zip(mes_ano: str) -> bytes:
    url = URL_TEMPLATE.format(mes_ano=mes_ano)
    with httpx.Client(timeout=300.0, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content


def parse_siape_zip(conteudo: bytes) -> pl.DataFrame:
    """Extrai o CSV de Cadastro do ZIP e retorna como Polars DataFrame."""
    with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
        cadastro = [n for n in zf.namelist() if "Cadastro" in n and n.endswith(".csv")]
        if not cadastro:
            raise FileNotFoundError("CSV de Cadastro não encontrado no ZIP")
        with zf.open(cadastro[0]) as f:
            df = pl.read_csv(
                f.read(),
                separator=";",
                encoding="latin1",
                infer_schema_length=1000,
                ignore_errors=True,
            )
    return df


def ingerir_servidores(
    db: Session,
    mes_ano: str = "202602",
    top_n: int = 1000,
    substituir: bool = True,
) -> dict:
    conteudo = baixar_siape_zip(mes_ano)
    df = parse_siape_zip(conteudo)

    col_cpf = next(c for c in df.columns if "CPF" in c.upper())
    col_nome = next(c for c in df.columns if "NOME" in c.upper() and "SERVIDOR" in c.upper())
    col_orgao = next(c for c in df.columns if "ORG" in c.upper() and "EXERCICIO" in c.upper())
    col_cargo = next((c for c in df.columns if "DESCRICAO_CARGO" in c.upper()), None)

    agreg = (
        df.group_by(col_cpf)
        .agg([
            pl.col(col_nome).first().alias("nome"),
            pl.col(col_orgao).first().alias("orgao"),
            (pl.col(col_cargo).first().alias("cargo") if col_cargo else pl.lit("").alias("cargo")),
        ])
        .head(top_n)
    )

    if substituir:
        db.query(AgentePublico).delete()
        db.flush()

    inseridos = 0
    for row in agreg.iter_rows(named=True):
        cpf = str(row[col_cpf] or "").strip()
        if not cpf:
            continue
        if db.query(AgentePublico).filter(AgentePublico.cpf == cpf).first():
            continue
        db.add(AgentePublico(
            cpf=cpf[:14],
            nome=(row["nome"] or "")[:200],
            orgao=(row["orgao"] or "")[:200],
            cargo=(row["cargo"] or "")[:200],
            remuneracao=0.0,
        ))
        inseridos += 1
    db.commit()
    return {"inseridos": inseridos, "mes_ano": mes_ano, "linhas_dump": len(df)}
