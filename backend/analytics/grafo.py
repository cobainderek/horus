"""Grafo de relacionamentos (NetworkX).

Apache AGE está disponível como extensão no Postgres (ver docker-compose),
mas o cálculo de métricas é feito em Python via NetworkX, que é mais
prático para análises ad-hoc e exportação pro frontend.
"""
from __future__ import annotations

import networkx as nx
from sqlalchemy import text
from sqlalchemy.orm import Session


def construir_grafo(db: Session, valor_min_contrato: float = 0.0) -> nx.DiGraph:
    """Constrói grafo direcionado a partir das tabelas relacionais.

    Nós:
      - agente:{cpf}    (servidor público)
      - empresa:{cnpj}  (pessoa jurídica)
      - orgao:{nome}    (órgão contratante)

    Arestas:
      - agente --SOCIO--> empresa
      - empresa --CONTRATO--> orgao   (com valor)
      - empresa --CEIS--> orgao_sancionador
      - empresa --DOOU--> agente (via doação eleitoral)
    """
    g = nx.DiGraph()

    for r in db.execute(text("SELECT cpf, nome, orgao FROM agentes_publicos")).fetchall():
        g.add_node(f"agente:{r.cpf}", kind="agente", label=r.nome, orgao=r.orgao)

    for r in db.execute(text("SELECT cnpj, razao_social, score_risco FROM empresas")).fetchall():
        g.add_node(
            f"empresa:{r.cnpj}",
            kind="empresa",
            label=r.razao_social,
            score=float(r.score_risco or 0),
        )

    for r in db.execute(text("""
        SELECT DISTINCT orgao_contratante FROM contratos_publicos
    """)).fetchall():
        g.add_node(f"orgao:{r.orgao_contratante}", kind="orgao", label=r.orgao_contratante)

    for r in db.execute(text("""
        SELECT cpf_socio, cnpj_empresa, qualificacao FROM socios_empresa
    """)).fetchall():
        u = f"agente:{r.cpf_socio}"
        v = f"empresa:{r.cnpj_empresa}"
        if u in g and v in g:
            g.add_edge(u, v, kind="SOCIO", qualificacao=r.qualificacao)

    for r in db.execute(
        text("""
            SELECT cnpj_fornecedor, orgao_contratante, valor
              FROM contratos_publicos
             WHERE valor >= :v
        """),
        {"v": valor_min_contrato},
    ).fetchall():
        u = f"empresa:{r.cnpj_fornecedor}"
        v = f"orgao:{r.orgao_contratante}"
        if u in g and v in g:
            if g.has_edge(u, v):
                g[u][v]["valor_total"] += float(r.valor or 0)
                g[u][v]["n"] += 1
            else:
                g.add_edge(u, v, kind="CONTRATO", valor_total=float(r.valor or 0), n=1)

    for r in db.execute(text("""
        SELECT cnpj_doador, cpf_candidato, valor FROM doacoes_eleitorais
    """)).fetchall():
        u = f"empresa:{r.cnpj_doador}"
        v = f"agente:{r.cpf_candidato}"
        if u in g and v in g:
            g.add_edge(u, v, kind="DOOU", valor=float(r.valor or 0))

    return g


def metricas_grafo(g: nx.DiGraph) -> dict:
    if g.number_of_nodes() == 0:
        return {"vazio": True}

    grau_central = nx.degree_centrality(g)
    top = sorted(grau_central.items(), key=lambda x: x[1], reverse=True)[:10]
    return {
        "n_nos": g.number_of_nodes(),
        "n_arestas": g.number_of_edges(),
        "n_componentes": nx.number_weakly_connected_components(g),
        "top_centralidade_grau": [
            {
                "id": n,
                "label": g.nodes[n].get("label"),
                "kind": g.nodes[n].get("kind"),
                "centralidade": round(c, 4),
            }
            for n, c in top
        ],
    }


def grafo_para_d3(g: nx.DiGraph) -> dict:
    nodes = [
        {"id": n, **{k: v for k, v in g.nodes[n].items() if k != "id"}}
        for n in g.nodes
    ]
    links = [
        {"source": u, "target": v, **{k: w for k, w in g.edges[u, v].items()}}
        for u, v in g.edges
    ]
    return {"nodes": nodes, "links": links}
