"""Pipeline ETL — duas camadas: API → CSV (bronze) → BD (silver).

Uso:
    # baixar (API → CSV em data/raw/)
    python -m backend.ingestao baixar-ceis [--paginas N]
    python -m backend.ingestao baixar-contratos [--max-empresas N] [--paginas N]

    # carregar (CSV → BD)
    python -m backend.ingestao carregar-ceis [--csv PATH]
    python -m backend.ingestao carregar-contratos [--csv PATH]

    # fluxo completo (baixa CEIS, carrega, baixa contratos das sancionadas, carrega)
    python -m backend.ingestao tudo [--paginas N] [--max-empresas N]

    # inspeção
    python -m backend.ingestao listar-csvs

    # fontes secundárias (mesma ideia, mas baixa direto pro BD por enquanto)
    python -m backend.ingestao servidores [--mes-ano AAAAMM] [--top N]
    python -m backend.ingestao qsa
    python -m backend.ingestao doacoes
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from .api import models  # noqa: F401 — registra tabelas em Base.metadata
from .api.database import Base, SessionLocal, aplicar_migrations, engine
from .ingestao_lib import brasilapi, cgu

load_dotenv()


def _setup_db() -> None:
    Base.metadata.create_all(bind=engine)
    aplicar_migrations()


# ─── baixar (API → CSV) ───────────────────────────────────────────────────

def cmd_baixar_ceis(args) -> dict:
    print(f"  → baixando CEIS ({args.paginas} páginas)...")
    return cgu.baixar_ceis_csv(max_paginas=args.paginas)


def cmd_baixar_contratos(args) -> dict:
    from .api.models import CEIS, Empresa
    with SessionLocal() as db:
        cnpjs = [
            c[0]
            for c in db.query(Empresa.cnpj)
            .join(CEIS, CEIS.cnpj == Empresa.cnpj)
            .distinct()
            .all()
        ]
    if args.max_empresas:
        cnpjs = cnpjs[: args.max_empresas]
    if not cnpjs:
        print("  ! nenhuma empresa sancionada no banco — rode carregar-ceis antes")
        sys.exit(1)
    print(f"  → baixando contratos de {len(cnpjs)} empresas...")
    return cgu.baixar_contratos_csv(cnpjs, max_paginas_por_empresa=args.paginas)


# ─── carregar (CSV → BD) ──────────────────────────────────────────────────

def cmd_carregar_ceis(args) -> dict:
    path = Path(args.csv) if args.csv else None
    with SessionLocal() as db:
        return cgu.carregar_ceis_csv(db, path)


def cmd_carregar_contratos(args) -> dict:
    path = Path(args.csv) if args.csv else None
    with SessionLocal() as db:
        return cgu.carregar_contratos_csv(db, path)


def cmd_baixar_empresas(args) -> dict:
    from .api.models import Empresa
    with SessionLocal() as db:
        cnpjs = [c[0] for c in db.query(Empresa.cnpj).distinct().all()]
    if args.max_empresas:
        cnpjs = cnpjs[: args.max_empresas]
    print(f"  → baixando dados de {len(cnpjs)} empresas via BrasilAPI...")
    return brasilapi.baixar_empresas_csv(cnpjs, sleep_segundos=args.sleep)


def cmd_carregar_empresas(args) -> dict:
    emp_path = Path(args.csv_empresas) if args.csv_empresas else None
    soc_path = Path(args.csv_socios) if args.csv_socios else None
    with SessionLocal() as db:
        r_emp = brasilapi.carregar_empresas_csv(db, emp_path)
        r_soc = brasilapi.carregar_socios_csv(db, soc_path)
    return {"empresas": r_emp, "socios": r_soc}


# ─── tudo (fluxo completo) ────────────────────────────────────────────────

def cmd_tudo(args) -> dict:
    """Pipeline completo: 6 passos, CEIS + Contratos + BrasilAPI."""
    resultados = {}

    print("[1/6] baixar CEIS (CGU → CSV)")
    try:
        r = cgu.baixar_ceis_csv(max_paginas=args.paginas)
    except cgu.APIKeyError as e:
        print(f"      ✗ {e}", file=sys.stderr)
        sys.exit(1)
    print(f"      ✓ {r['csv']} — {r['linhas']} linhas")
    resultados["baixar_ceis"] = r

    print("[2/6] carregar CEIS (CSV → BD)")
    with SessionLocal() as db:
        r = cgu.carregar_ceis_csv(db, Path(resultados["baixar_ceis"]["csv"]))
    print(f"      ✓ inseridos={r['inseridos']} atualizados={r['atualizados']}")
    resultados["carregar_ceis"] = r

    print("[3/6] baixar contratos das sancionadas (CGU → CSV)")
    from .api.models import CEIS, Empresa
    with SessionLocal() as db:
        cnpjs = [
            c[0]
            for c in db.query(Empresa.cnpj)
            .join(CEIS, CEIS.cnpj == Empresa.cnpj)
            .distinct()
            .all()
        ]
    if args.max_empresas:
        cnpjs = cnpjs[: args.max_empresas]
    print(f"      → {len(cnpjs)} CNPJs a consultar")
    r = cgu.baixar_contratos_csv(cnpjs, max_paginas_por_empresa=args.paginas_contrato)
    print(f"      ✓ {r['csv']} — {r['linhas']} linhas")
    resultados["baixar_contratos"] = r

    print("[4/6] carregar contratos (CSV → BD)")
    with SessionLocal() as db:
        r = cgu.carregar_contratos_csv(db, Path(resultados["baixar_contratos"]["csv"]))
    print(f"      ✓ inseridos={r['inseridos']} atualizados={r['atualizados']}")
    resultados["carregar_contratos"] = r

    print(f"[5/6] baixar dados cadastrais (BrasilAPI → CSV) — {len(cnpjs)} CNPJs")
    r = brasilapi.baixar_empresas_csv(cnpjs, sleep_segundos=args.sleep_brasilapi)
    print(f"      ✓ {r['encontradas']}/{r['consultadas']} OK · {r['erros']} erros · {r['socios']} sócios")
    resultados["baixar_empresas"] = r

    print("[6/6] carregar dados cadastrais + sócios (CSV → BD)")
    with SessionLocal() as db:
        r_emp = brasilapi.carregar_empresas_csv(db, Path(resultados["baixar_empresas"]["csv_empresas"]))
        r_soc = brasilapi.carregar_socios_csv(db, Path(resultados["baixar_empresas"]["csv_socios"]))
    print(f"      ✓ empresas: inseridas={r_emp['inseridos']} atualizadas={r_emp['atualizados']} · sócios: inseridos={r_soc['inseridos']}")
    resultados["carregar_empresas"] = r_emp
    resultados["carregar_socios"] = r_soc

    return resultados


# ─── inspeção ─────────────────────────────────────────────────────────────

def cmd_listar_csvs(args) -> None:
    if not cgu.RAW_DIR.exists():
        print(f"  (vazio) — diretório {cgu.RAW_DIR} ainda não foi criado")
        return
    csvs = sorted(cgu.RAW_DIR.glob("*.csv"))
    if not csvs:
        print(f"  (vazio) — nenhum CSV em {cgu.RAW_DIR}")
        return
    print(f"  CSVs em {cgu.RAW_DIR}:")
    for f in csvs:
        size = f.stat().st_size
        # contar linhas (rápido — só pra dataset pequeno)
        try:
            linhas = sum(1 for _ in open(f, encoding="utf-8")) - 1
        except Exception:
            linhas = "?"
        print(f"    {f.name:40s}  {size:>10} bytes  {linhas:>6} linhas")


# ─── fontes secundárias (legadas, ainda direto pro BD) ───────────────────

def cmd_servidores(args) -> dict:
    from .ingestao_lib.siape import ingerir_servidores
    with SessionLocal() as db:
        return ingerir_servidores(db, mes_ano=args.mes_ano, top_n=args.top, substituir=True)


def cmd_qsa(args) -> dict:
    from .ingestao_lib.brasilapi import ingerir_qsa
    with SessionLocal() as db:
        return ingerir_qsa(db, max_empresas=args.max_empresas, sleep_segundos=args.sleep)


def cmd_doacoes(args) -> dict:
    from .ingestao_lib.tse import ingerir_doacoes
    with SessionLocal() as db:
        return ingerir_doacoes(db, url=args.url, csv_local_path=args.csv_local)


# ─── CLI ─────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Hórus — ETL (API → CSV → BD)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # bronze: API → CSV
    p = sub.add_parser("baixar-ceis", help="baixa CEIS da CGU e grava em data/raw/ceis_*.csv")
    p.add_argument("--paginas", type=int, default=30)
    p.set_defaults(func=cmd_baixar_ceis)

    p = sub.add_parser("baixar-contratos", help="baixa contratos das sancionadas e grava CSV")
    p.add_argument("--max-empresas", type=int, default=None)
    p.add_argument("--paginas", type=int, default=2)
    p.set_defaults(func=cmd_baixar_contratos)

    # silver: CSV → BD
    p = sub.add_parser("carregar-ceis", help="carrega data/raw/ceis_*.csv no banco")
    p.add_argument("--csv", default=None, help="path do CSV (default: data/raw/ceis_HOJE.csv)")
    p.set_defaults(func=cmd_carregar_ceis)

    p = sub.add_parser("carregar-contratos", help="carrega data/raw/contratos_*.csv no banco")
    p.add_argument("--csv", default=None)
    p.set_defaults(func=cmd_carregar_contratos)

    # bronze/silver BrasilAPI
    p = sub.add_parser("baixar-empresas", help="baixa dados cadastrais da Receita (BrasilAPI) e grava CSV + sócios")
    p.add_argument("--max-empresas", type=int, default=None)
    p.add_argument("--sleep", type=float, default=0.5)
    p.set_defaults(func=cmd_baixar_empresas)

    p = sub.add_parser("carregar-empresas", help="carrega data/raw/empresas_brasilapi_*.csv + socios_*.csv")
    p.add_argument("--csv-empresas", default=None)
    p.add_argument("--csv-socios", default=None)
    p.set_defaults(func=cmd_carregar_empresas)

    # fluxo completo
    p = sub.add_parser("tudo", help="fluxo completo: CEIS + contratos + BrasilAPI (6 passos)")
    p.add_argument("--paginas", type=int, default=50, help="páginas CEIS (default 50)")
    p.add_argument("--paginas-contrato", type=int, default=2, help="páginas por empresa em contratos")
    p.add_argument("--max-empresas", type=int, default=None, help="limita empresas pra contratos+BrasilAPI")
    p.add_argument("--sleep-brasilapi", type=float, default=0.8, help="pausa entre chamadas BrasilAPI (rate-limit)")
    p.set_defaults(func=cmd_tudo)

    # inspeção
    p = sub.add_parser("listar-csvs", help="lista CSVs em data/raw/")
    p.set_defaults(func=cmd_listar_csvs)

    # fontes secundárias (sem CSV intermediário por enquanto)
    p = sub.add_parser("servidores", help="ingere SIAPE direto pro banco")
    p.add_argument("--mes-ano", default="202602")
    p.add_argument("--top", type=int, default=1000)
    p.set_defaults(func=cmd_servidores)

    p = sub.add_parser("qsa", help="ingere QSA via BrasilAPI direto pro banco")
    p.add_argument("--max-empresas", type=int, default=None)
    p.add_argument("--sleep", type=float, default=0.5)
    p.set_defaults(func=cmd_qsa)

    p = sub.add_parser("doacoes", help="ingere doações TSE direto pro banco")
    p.add_argument(
        "--url",
        default="https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2022.zip",
    )
    p.add_argument("--csv-local", default=None)
    p.set_defaults(func=cmd_doacoes)

    args = parser.parse_args()
    _setup_db()
    resultado = args.func(args)
    if resultado is not None:
        print(resultado)


if __name__ == "__main__":
    main()
