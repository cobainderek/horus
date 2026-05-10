"""Script 2 — cruza os dados no banco e imprime/exporta resultados.

Uso:
    python -m backend.cruzamento conflito                  # cruzamento 1 (CPF)
    python -m backend.cruzamento conflito-nome             # cruzamento 1 (fuzzy)
    python -m backend.cruzamento retorno-favor             # cruzamento 2
    python -m backend.cruzamento empresa-sancionada        # cruzamento 5
    python -m backend.cruzamento todos                     # roda tudo
    python -m backend.cruzamento score                     # recalcula scores
    python -m backend.cruzamento ml-treinar                # treina Isolation Forest
    python -m backend.cruzamento ml-anomalias              # top 20 anomalias

Saída: tabela no stdout + JSON opcional (--out FILE).
"""
from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv
from sqlalchemy import text

from .analytics.fuzzy_match import cruzar_agentes_socios_por_nome
from .analytics.isolation_forest import prever_anomalias, treinar_modelo
from .analytics.score import atualizar_todos_scores
from .api.database import Base, SessionLocal, engine

load_dotenv()


def _conflito_cpf(db) -> list[dict]:
    rows = db.execute(text("""
        SELECT a.nome AS agente, a.cpf, a.orgao AS agente_orgao,
               e.razao_social AS empresa, e.cnpj,
               c.valor, c.orgao_contratante, c.objeto
          FROM agentes_publicos a
          JOIN socios_empresa s ON s.cpf_socio = a.cpf
          JOIN empresas e ON e.cnpj = s.cnpj_empresa
          JOIN contratos_publicos c ON c.cnpj_fornecedor = e.cnpj
         WHERE LOWER(c.orgao_contratante) LIKE '%' || LOWER(a.orgao) || '%'
         ORDER BY c.valor DESC
    """)).fetchall()
    return [dict(r._mapping) for r in rows]


def _retorno_favor(db) -> list[dict]:
    rows = db.execute(text("""
        SELECT d.nome_doador, d.cnpj_doador, d.valor AS doacao,
               d.ano_eleicao, d.nome_candidato,
               c.valor AS contrato, c.orgao_contratante, c.objeto
          FROM doacoes_eleitorais d
          JOIN contratos_publicos c ON c.cnpj_fornecedor = d.cnpj_doador
         ORDER BY c.valor DESC
    """)).fetchall()
    return [dict(r._mapping) for r in rows]


def _empresa_sancionada(db) -> list[dict]:
    rows = db.execute(text("""
        SELECT ce.razao_social, ce.cnpj, ce.tipo_sancao,
               c.valor, c.orgao_contratante, c.objeto
          FROM ceis ce
          JOIN contratos_publicos c ON c.cnpj_fornecedor = ce.cnpj
         ORDER BY c.valor DESC
    """)).fetchall()
    return [dict(r._mapping) for r in rows]


def _imprimir(titulo: str, linhas: list[dict], limite: int = 20) -> None:
    print(f"\n=== {titulo} ({len(linhas)} resultados) ===")
    for l in linhas[:limite]:
        chaves = list(l.keys())
        resumo = " | ".join(f"{k}={l[k]}" for k in chaves[:4] if l[k] is not None)
        print(f"  • {resumo}")
    if len(linhas) > limite:
        print(f"  ... e mais {len(linhas) - limite} resultado(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hórus — cruzamentos")
    parser.add_argument(
        "cmd",
        choices=[
            "conflito", "conflito-nome", "retorno-favor", "empresa-sancionada",
            "todos", "score", "ml-treinar", "ml-anomalias",
        ],
    )
    parser.add_argument("--threshold", type=int, default=90, help="fuzzy match")
    parser.add_argument("--limite", type=int, default=20)
    parser.add_argument("--out", default=None, help="exportar JSON para esse caminho")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        resultado = None

        if args.cmd == "conflito":
            resultado = _conflito_cpf(db)
            _imprimir("Conflito de interesse (CPF)", resultado, args.limite)
        elif args.cmd == "conflito-nome":
            resultado = cruzar_agentes_socios_por_nome(db, threshold=args.threshold)
            _imprimir("Conflito de interesse (fuzzy match)", resultado, args.limite)
        elif args.cmd == "retorno-favor":
            resultado = _retorno_favor(db)
            _imprimir("Retorno de favor", resultado, args.limite)
        elif args.cmd == "empresa-sancionada":
            resultado = _empresa_sancionada(db)
            _imprimir("Empresa sancionada com contrato", resultado, args.limite)
        elif args.cmd == "todos":
            resultado = {
                "conflito": _conflito_cpf(db),
                "retorno_favor": _retorno_favor(db),
                "empresa_sancionada": _empresa_sancionada(db),
            }
            for k, v in resultado.items():
                _imprimir(k, v, args.limite)
        elif args.cmd == "score":
            resultado = atualizar_todos_scores(db)
            print(resultado)
        elif args.cmd == "ml-treinar":
            try:
                resultado = treinar_modelo(db)
                print(resultado)
            except ValueError as e:
                print(f"✗ {e}", file=sys.stderr)
                sys.exit(1)
        elif args.cmd == "ml-anomalias":
            try:
                resultado = prever_anomalias(db, top_n=args.limite)
                _imprimir("Top anomalias (Isolation Forest)", resultado, args.limite)
            except FileNotFoundError as e:
                print(f"✗ {e}", file=sys.stderr)
                sys.exit(1)

        if args.out and resultado is not None:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n✓ exportado para {args.out}")


if __name__ == "__main__":
    main()
