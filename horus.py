"""
Hórus — Sistema de fiscalização pública (MVP)

Pipeline único: baixa CEIS da CGU, baixa contratos das empresas sancionadas,
roda 1 cruzamento (CEIS × Contratos) e escreve `dados.json` para a página.

Uso:
    python horus.py                    # ingere + analisa + escreve dados.json
    python horus.py --so-analise       # pula ingestão (banco já populado)
    python horus.py --paginas 50       # quantas páginas de CEIS baixar (default 30)
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime

import httpx
from dotenv import load_dotenv
from sqlalchemy import (
    Column, Float, ForeignKey, Integer, String, Text, create_engine, text,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker


# ─── CONFIG ──────────────────────────────────────────────────────────────

load_dotenv()
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://horus:horus123@localhost:5433/horus",
)
API_KEY = os.getenv("API_PORTAL_TRANSPARENCIA_KEY", "").strip()
BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"
TIMEOUT = 30.0
OUT_JSON = "dados.json"


# ─── MODELOS ─────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class Empresa(Base):
    __tablename__ = "empresas"
    cnpj = Column(String(18), primary_key=True)
    razao_social = Column(String(300), nullable=False)
    sancoes = relationship("CEIS", back_populates="empresa")
    contratos = relationship("ContratoPublico", back_populates="empresa")


class CEIS(Base):
    __tablename__ = "ceis"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(18), ForeignKey("empresas.cnpj"), nullable=False)
    razao_social = Column(String(300))
    tipo_sancao = Column(String(200))
    data_inicio_sancao = Column(String(10))
    data_fim_sancao = Column(String(10))
    orgao_sancionador = Column(String(200))
    empresa = relationship("Empresa", back_populates="sancoes")


class ContratoPublico(Base):
    __tablename__ = "contratos_publicos"
    id = Column(String(20), primary_key=True)
    cnpj_fornecedor = Column(String(18), ForeignKey("empresas.cnpj"), nullable=False)
    orgao_contratante = Column(String(200), nullable=False)
    valor = Column(Float, nullable=False)
    data_inicio = Column(String(10))
    data_fim = Column(String(10))
    objeto = Column(Text)
    empresa = relationship("Empresa", back_populates="contratos")


# ─── HTTP ─────────────────────────────────────────────────────────────────

class APIKeyError(RuntimeError):
    pass


def _headers() -> dict:
    if not API_KEY:
        raise APIKeyError(
            "API_PORTAL_TRANSPARENCIA_KEY não definida no .env. "
            "Cadastre uma chave gratuita em "
            "https://portaldatransparencia.gov.br/api-de-dados/cadastrar"
        )
    return {"chave-api-dados": API_KEY, "Accept": "application/json"}


def _so_digitos(s: str) -> str:
    return "".join(c for c in (s or "") if c.isdigit())


def _data_br_para_iso(s: str | None) -> str | None:
    if not s or s.strip().lower() == "sem informação":
        return None
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def buscar_ceis(client: httpx.Client, pagina: int) -> list[dict]:
    r = client.get(f"{BASE_URL}/ceis", headers=_headers(), params={"pagina": pagina})
    r.raise_for_status()
    return r.json()


def buscar_contratos(client: httpx.Client, cnpj: str, pagina: int = 1) -> list[dict]:
    r = client.get(
        f"{BASE_URL}/contratos/cpf-cnpj",
        headers=_headers(),
        params={"cpfCnpj": _so_digitos(cnpj), "pagina": pagina},
    )
    r.raise_for_status()
    return r.json()


# ─── PARSING ─────────────────────────────────────────────────────────────

def parse_ceis(item: dict) -> dict | None:
    pessoa = item.get("pessoa") or {}
    cnpj = (pessoa.get("cnpjFormatado") or "").strip()
    if not cnpj:
        return None
    razao = (
        pessoa.get("razaoSocialReceita")
        or pessoa.get("nome")
        or (item.get("sancionado") or {}).get("nome")
        or "(sem razão social)"
    ).strip()
    return {
        "cnpj": cnpj,
        "razao_social": razao[:300],
        "tipo_sancao": (item.get("tipoSancao") or {}).get("descricaoResumida", "")[:200],
        "data_inicio_sancao": _data_br_para_iso(item.get("dataInicioSancao")),
        "data_fim_sancao": _data_br_para_iso(item.get("dataFimSancao")),
        "orgao_sancionador": (item.get("orgaoSancionador") or {}).get("nome", "")[:200],
    }


def parse_contrato(item: dict) -> dict | None:
    fornecedor = item.get("fornecedor") or {}
    cnpj = (fornecedor.get("cnpjFormatado") or "").strip()
    if not cnpj:
        return None
    unidade = item.get("unidadeGestora") or {}
    orgao_max = unidade.get("orgaoMaximo") or {}
    orgao_vinc = unidade.get("orgaoVinculado") or {}
    orgao_nome = (orgao_max.get("nome") or orgao_vinc.get("nome") or "").strip()
    valor = item.get("valorFinalCompra") or item.get("valorInicialCompra") or 0.0
    return {
        "id": str(item.get("id") or "")[:20],
        "cnpj_fornecedor": cnpj,
        "orgao_contratante": orgao_nome[:200] or "(sem informação)",
        "valor": float(valor),
        "data_inicio": (item.get("dataInicioVigencia") or "")[:10] or None,
        "data_fim": (item.get("dataFimVigencia") or "")[:10] or None,
        "objeto": (item.get("objeto") or "")[:2000],
        "_razao_social": (
            fornecedor.get("razaoSocialReceita") or fornecedor.get("nome") or ""
        ).strip()[:300],
    }


# ─── PERSISTÊNCIA ────────────────────────────────────────────────────────

def upsert_empresa(db: Session, cnpj: str, razao_social: str) -> None:
    if db.query(Empresa).filter(Empresa.cnpj == cnpj).first() is None:
        db.add(Empresa(cnpj=cnpj, razao_social=razao_social))
        db.flush()


def ingerir_ceis(db: Session, max_paginas: int = 30) -> dict:
    print(f"  → baixando CEIS ({max_paginas} páginas, 15 itens/página)...")
    inseridos = duplicados = pulados = 0
    with httpx.Client(timeout=TIMEOUT) as client:
        for pagina in range(1, max_paginas + 1):
            itens = buscar_ceis(client, pagina)
            if not itens:
                break
            for item in itens:
                parsed = parse_ceis(item)
                if parsed is None:
                    pulados += 1
                    continue
                ja = db.query(CEIS).filter(
                    CEIS.cnpj == parsed["cnpj"],
                    CEIS.data_inicio_sancao == parsed["data_inicio_sancao"],
                    CEIS.tipo_sancao == parsed["tipo_sancao"],
                ).first()
                if ja:
                    duplicados += 1
                    continue
                upsert_empresa(db, parsed["cnpj"], parsed["razao_social"])
                db.add(CEIS(**parsed))
                inseridos += 1
            print(f"    pag {pagina:>3}: {len(itens):>2} itens (+{inseridos} acum)")
            if pagina < max_paginas:
                time.sleep(0.5)
    db.commit()
    return {"inseridos": inseridos, "duplicados": duplicados, "pulados_pf": pulados}


def ingerir_contratos_sancionados(db: Session, max_paginas_por_empresa: int = 2) -> dict:
    cnpjs = [
        c[0]
        for c in db.query(Empresa.cnpj)
        .join(CEIS, CEIS.cnpj == Empresa.cnpj)
        .distinct()
        .all()
    ]
    print(f"  → buscando contratos de {len(cnpjs)} empresas sancionadas...")
    totais = {
        "inseridos": 0,
        "duplicados": 0,
        "ignorados": 0,
        "empresas_com_contrato": 0,
        "empresas_consultadas": 0,
        "erros": 0,
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        for i, cnpj in enumerate(cnpjs, 1):
            totais["empresas_consultadas"] += 1
            inseridos_emp = 0
            for pagina in range(1, max_paginas_por_empresa + 1):
                try:
                    itens = buscar_contratos(client, cnpj, pagina)
                except httpx.HTTPStatusError as e:
                    totais["erros"] += 1
                    print(f"    ! {cnpj} pag {pagina}: {e.response.status_code}")
                    break
                except httpx.HTTPError as e:
                    totais["erros"] += 1
                    print(f"    ! {cnpj} pag {pagina}: {type(e).__name__}")
                    break
                if not itens:
                    break
                for item in itens:
                    parsed = parse_contrato(item)
                    if parsed is None or not parsed["id"]:
                        totais["ignorados"] += 1
                        continue
                    if db.query(ContratoPublico).filter(
                        ContratoPublico.id == parsed["id"]
                    ).first():
                        totais["duplicados"] += 1
                        continue
                    razao = parsed.pop("_razao_social") or "(sem razão social)"
                    upsert_empresa(db, parsed["cnpj_fornecedor"], razao)
                    db.add(ContratoPublico(**parsed))
                    totais["inseridos"] += 1
                    inseridos_emp += 1
                time.sleep(0.4)
            if inseridos_emp:
                totais["empresas_com_contrato"] += 1
            if i % 20 == 0:
                print(
                    f"    {i:>3}/{len(cnpjs)} empresas consultadas "
                    f"(+{totais['inseridos']} contratos)"
                )
    db.commit()
    return totais


# ─── ANÁLISE ─────────────────────────────────────────────────────────────

def analisar(db: Session) -> dict:
    print("  → cruzando CEIS × Contratos e gerando estatísticas...")

    total_empresas_ceis = db.execute(
        text("SELECT COUNT(DISTINCT cnpj) FROM ceis")
    ).scalar() or 0
    total_contratos = db.execute(
        text("SELECT COUNT(*) FROM contratos_publicos")
    ).scalar() or 0

    irregularidades = db.execute(text("""
        SELECT
            e.cnpj,
            e.razao_social,
            COUNT(DISTINCT c.id) AS n_contratos,
            COALESCE(SUM(c.valor), 0) AS valor_total,
            STRING_AGG(DISTINCT ce.tipo_sancao, ' | ') AS sancoes,
            STRING_AGG(DISTINCT c.orgao_contratante, ' | ') AS orgaos
        FROM empresas e
        JOIN ceis ce ON ce.cnpj = e.cnpj
        JOIN contratos_publicos c ON c.cnpj_fornecedor = e.cnpj
        GROUP BY e.cnpj, e.razao_social
        ORDER BY valor_total DESC
    """)).fetchall()

    n_irregulares = len(irregularidades)
    valor_total = sum(float(r.valor_total) for r in irregularidades)
    valores = [float(r.valor_total) for r in irregularidades if r.valor_total > 0]

    if valores:
        stats_valores = {
            "media": round(statistics.mean(valores), 2),
            "mediana": round(statistics.median(valores), 2),
            "minimo": round(min(valores), 2),
            "maximo": round(max(valores), 2),
            "desvio_padrao": round(statistics.pstdev(valores), 2) if len(valores) > 1 else 0.0,
        }
    else:
        stats_valores = {"media": 0, "mediana": 0, "minimo": 0, "maximo": 0, "desvio_padrao": 0}

    top_orgaos = db.execute(text("""
        SELECT
            c.orgao_contratante AS orgao,
            COUNT(DISTINCT c.id) AS n_contratos,
            COALESCE(SUM(c.valor), 0) AS valor_total
        FROM contratos_publicos c
        JOIN ceis ce ON ce.cnpj = c.cnpj_fornecedor
        GROUP BY c.orgao_contratante
        ORDER BY valor_total DESC
        LIMIT 10
    """)).fetchall()

    tipos_sancao = db.execute(text("""
        SELECT tipo_sancao, COUNT(*) AS quantidade
        FROM ceis
        WHERE tipo_sancao IS NOT NULL AND tipo_sancao != ''
        GROUP BY tipo_sancao
        ORDER BY quantidade DESC
    """)).fetchall()

    pct = (n_irregulares / total_empresas_ceis * 100) if total_empresas_ceis else 0

    return {
        "gerado_em": datetime.now().isoformat(),
        "kpis": {
            "total_empresas_ceis": int(total_empresas_ceis),
            "empresas_irregulares": int(n_irregulares),
            "total_contratos_no_banco": int(total_contratos),
            "valor_total_suspeito": round(valor_total, 2),
            "percentual_ceis_com_contrato": round(pct, 2),
        },
        "estatisticas_valores": stats_valores,
        "top_empresas": [
            {
                "cnpj": r.cnpj,
                "razao_social": r.razao_social,
                "n_contratos": int(r.n_contratos),
                "valor_total": round(float(r.valor_total), 2),
                "sancoes": r.sancoes or "",
                "orgaos": r.orgaos or "",
            }
            for r in irregularidades[:20]
        ],
        "top_orgaos": [
            {
                "orgao": r.orgao,
                "n_contratos": int(r.n_contratos),
                "valor_total": round(float(r.valor_total), 2),
            }
            for r in top_orgaos
        ],
        "distribuicao_sancoes": [
            {"tipo": r.tipo_sancao or "(sem tipo)", "quantidade": int(r.quantidade)}
            for r in tipos_sancao
        ],
    }


# ─── CLI ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hórus — pipeline CEIS × Contratos Federais"
    )
    parser.add_argument(
        "--so-analise", action="store_true",
        help="pula ingestão e só roda a análise sobre dados já no banco",
    )
    parser.add_argument(
        "--paginas", type=int, default=30,
        help="quantas páginas do CEIS baixar (default 30, 15 itens/pág)",
    )
    parser.add_argument(
        "--paginas-contrato", type=int, default=2,
        help="quantas páginas de contrato por empresa (default 2)",
    )
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    with SessionLocal() as db:
        if not args.so_analise:
            print("[1/3] ingestão CEIS")
            try:
                r = ingerir_ceis(db, max_paginas=args.paginas)
            except APIKeyError as e:
                print(f"      ✗ {e}", file=sys.stderr)
                sys.exit(1)
            print(
                f"      ✓ inseridos={r['inseridos']} "
                f"duplicados={r['duplicados']} pulados_pf={r['pulados_pf']}"
            )

            print("[2/3] ingestão contratos das sancionadas")
            r = ingerir_contratos_sancionados(
                db, max_paginas_por_empresa=args.paginas_contrato
            )
            print(
                f"      ✓ consultadas={r['empresas_consultadas']} "
                f"com_contrato={r['empresas_com_contrato']} "
                f"inseridos={r['inseridos']} erros={r['erros']}"
            )
        else:
            print("[--so-analise] pulando ingestão")

        print("[3/3] análise e escrita do dados.json")
        dados = analisar(db)
        with open(OUT_JSON, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        k = dados["kpis"]
        print(
            f"      ✓ {OUT_JSON} — "
            f"{k['empresas_irregulares']} empresas irregulares, "
            f"R$ {k['valor_total_suspeito']:,.2f} suspeitos"
        )


if __name__ == "__main__":
    main()
