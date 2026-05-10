"""Ingestão de doações eleitorais TSE.

Baixa o ZIP da prestação de contas e filtra apenas doações de CNPJs já
presentes em `empresas`. Aceita URL remota ou caminho local.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import httpx
import polars as pl
from sqlalchemy.orm import Session

from ..api.models import DoacaoEleitoral, Empresa

URL_PADRAO_2022 = "https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2022.zip"


def _carregar_csv_receitas(conteudo: bytes) -> pl.DataFrame:
    with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
        nomes = [n for n in zf.namelist() if "receitas_candidatos" in n.lower() and n.endswith(".csv")]
        if not nomes:
            raise FileNotFoundError("CSV de receitas_candidatos não encontrado no ZIP")
        dfs = []
        for nome in nomes:
            with zf.open(nome) as f:
                df = pl.read_csv(
                    f.read(),
                    separator=";",
                    encoding="latin1",
                    infer_schema_length=1000,
                    ignore_errors=True,
                )
                dfs.append(df)
        return pl.concat(dfs, how="diagonal")


def ingerir_doacoes(
    db: Session,
    url: str = URL_PADRAO_2022,
    csv_local_path: str | None = None,
) -> dict:
    if csv_local_path:
        p = Path(csv_local_path)
        if p.suffix == ".zip":
            conteudo = p.read_bytes()
            df = _carregar_csv_receitas(conteudo)
        else:
            df = pl.read_csv(p, separator=";", encoding="latin1", ignore_errors=True)
    else:
        with httpx.Client(timeout=600.0, follow_redirects=True) as c:
            r = c.get(url)
            r.raise_for_status()
            df = _carregar_csv_receitas(r.content)

    cnpjs_banco = {c[0] for c in db.query(Empresa.cnpj).distinct().all()}

    col_cnpj = next((c for c in df.columns if "CNPJ" in c.upper() and ("DOADOR" in c.upper() or "ORIGEM" in c.upper())), None)
    if not col_cnpj:
        return {"inseridos": 0, "motivo": "coluna CNPJ doador não encontrada", "colunas": df.columns}

    col_nome_doador = next((c for c in df.columns if "NOME" in c.upper() and "DOADOR" in c.upper()), None)
    col_valor = next((c for c in df.columns if "VALOR" in c.upper() and "RECEITA" in c.upper()), None)
    col_cpf_cand = next((c for c in df.columns if "CPF_CANDIDATO" in c.upper().replace(" ", "_")), None)
    col_nome_cand = next((c for c in df.columns if "NOME_CANDIDATO" in c.upper().replace(" ", "_")), None)
    col_ano = next((c for c in df.columns if "ANO_ELEICAO" in c.upper().replace(" ", "_")), None)
    col_cargo = next((c for c in df.columns if "DESCRICAO_CARGO" in c.upper().replace(" ", "_") or "CARGO" in c.upper()), None)

    filtrado = df.filter(pl.col(col_cnpj).is_in(list(cnpjs_banco)))

    inseridos = 0
    for i, row in enumerate(filtrado.iter_rows(named=True)):
        rid = f"tse-{i}-{(row[col_cnpj] or '')[-8:]}"
        if db.query(DoacaoEleitoral).filter(DoacaoEleitoral.id == rid).first():
            continue
        try:
            valor = float(str(row[col_valor] or "0").replace(",", "."))
        except (ValueError, TypeError):
            valor = 0.0
        db.add(DoacaoEleitoral(
            id=rid[:20],
            cnpj_doador=(row[col_cnpj] or "")[:18],
            nome_doador=(row[col_nome_doador] or "")[:300] if col_nome_doador else "",
            cpf_candidato=(row[col_cpf_cand] or "")[:14] if col_cpf_cand else "",
            nome_candidato=(row[col_nome_cand] or "")[:200] if col_nome_cand else "",
            valor=valor,
            ano_eleicao=int(row[col_ano] or 0) if col_ano else 0,
            cargo_candidato=(row[col_cargo] or "")[:100] if col_cargo else "",
        ))
        inseridos += 1
    db.commit()
    return {"inseridos": inseridos, "doacoes_filtradas": len(filtrado), "empresas_no_banco": len(cnpjs_banco)}
