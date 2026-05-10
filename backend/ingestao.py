"""Script 1 — ingestão de dados públicos para o banco.

Uso:
    python -m backend.ingestao ceis [--paginas N]
    python -m backend.ingestao contratos [--max-empresas N] [--paginas N]
    python -m backend.ingestao servidores [--mes-ano AAAAMM] [--top N]
    python -m backend.ingestao qsa [--max-empresas N]
    python -m backend.ingestao doacoes [--csv-local PATH | --url URL]
    python -m backend.ingestao tudo

Cada subcomando é independente. `tudo` roda na ordem CEIS → contratos → SIAPE → QSA → doações.
"""
from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from .api.database import Base, SessionLocal, engine

load_dotenv()


def _setup_db() -> None:
    Base.metadata.create_all(bind=engine)


def cmd_ceis(args) -> dict:
    from .ingestao_lib.cgu import APIKeyError, ingerir_ceis
    with SessionLocal() as db:
        try:
            return ingerir_ceis(db, max_paginas=args.paginas)
        except APIKeyError as e:
            print(f"  ✗ {e}", file=sys.stderr)
            sys.exit(1)


def cmd_contratos(args) -> dict:
    from .ingestao_lib.cgu import ingerir_contratos_sancionados
    with SessionLocal() as db:
        return ingerir_contratos_sancionados(
            db,
            max_empresas=args.max_empresas,
            max_paginas_por_empresa=args.paginas,
        )


def cmd_servidores(args) -> dict:
    from .ingestao_lib.siape import ingerir_servidores
    with SessionLocal() as db:
        return ingerir_servidores(
            db,
            mes_ano=args.mes_ano,
            top_n=args.top,
            substituir=args.substituir,
        )


def cmd_qsa(args) -> dict:
    from .ingestao_lib.brasilapi import ingerir_qsa
    with SessionLocal() as db:
        return ingerir_qsa(
            db,
            max_empresas=args.max_empresas,
            sleep_segundos=args.sleep,
        )


def cmd_doacoes(args) -> dict:
    from .ingestao_lib.tse import ingerir_doacoes
    with SessionLocal() as db:
        return ingerir_doacoes(
            db,
            url=args.url,
            csv_local_path=args.csv_local,
        )


def cmd_tudo(args) -> dict:
    resultados = {}

    print("[1/5] CEIS")
    resultados["ceis"] = cmd_ceis(argparse.Namespace(paginas=args.paginas))
    print(f"      {resultados['ceis']}")

    print("[2/5] contratos das sancionadas")
    resultados["contratos"] = cmd_contratos(argparse.Namespace(
        max_empresas=None, paginas=2,
    ))
    print(f"      {resultados['contratos']}")

    print("[3/5] servidores SIAPE")
    try:
        resultados["servidores"] = cmd_servidores(argparse.Namespace(
            mes_ano="202602", top=1000, substituir=True,
        ))
        print(f"      {resultados['servidores']}")
    except Exception as e:  # noqa: BLE001
        print(f"      ✗ falhou: {e}")
        resultados["servidores"] = {"erro": str(e)}

    print("[4/5] QSA via BrasilAPI")
    try:
        resultados["qsa"] = cmd_qsa(argparse.Namespace(max_empresas=None, sleep=0.5))
        print(f"      {resultados['qsa']}")
    except Exception as e:  # noqa: BLE001
        print(f"      ✗ falhou: {e}")
        resultados["qsa"] = {"erro": str(e)}

    print("[5/5] doações TSE")
    try:
        resultados["doacoes"] = cmd_doacoes(argparse.Namespace(
            url="https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2022.zip",
            csv_local=None,
        ))
        print(f"      {resultados['doacoes']}")
    except Exception as e:  # noqa: BLE001
        print(f"      ✗ falhou: {e}")
        resultados["doacoes"] = {"erro": str(e)}

    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(description="Hórus — ingestão")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ceis", help="CEIS (CGU)")
    p.add_argument("--paginas", type=int, default=30)

    p = sub.add_parser("contratos", help="contratos das empresas sancionadas (CGU)")
    p.add_argument("--max-empresas", type=int, default=None)
    p.add_argument("--paginas", type=int, default=2)

    p = sub.add_parser("servidores", help="SIAPE — dump mensal")
    p.add_argument("--mes-ano", default="202602")
    p.add_argument("--top", type=int, default=1000)
    p.add_argument("--substituir", action="store_true", default=True)

    p = sub.add_parser("qsa", help="QSA via BrasilAPI")
    p.add_argument("--max-empresas", type=int, default=None)
    p.add_argument("--sleep", type=float, default=0.5)

    p = sub.add_parser("doacoes", help="doações eleitorais TSE")
    p.add_argument(
        "--url",
        default="https://cdn.tse.jus.br/estatistica/sead/odsele/prestacao_contas/prestacao_de_contas_eleitorais_candidatos_2022.zip",
    )
    p.add_argument("--csv-local", default=None)

    p = sub.add_parser("tudo", help="roda CEIS+contratos+SIAPE+QSA+doações em sequência")
    p.add_argument("--paginas", type=int, default=30)

    args = parser.parse_args()
    _setup_db()

    dispatch = {
        "ceis": cmd_ceis,
        "contratos": cmd_contratos,
        "servidores": cmd_servidores,
        "qsa": cmd_qsa,
        "doacoes": cmd_doacoes,
        "tudo": cmd_tudo,
    }
    resultado = dispatch[args.cmd](args)
    print(resultado)


if __name__ == "__main__":
    main()
