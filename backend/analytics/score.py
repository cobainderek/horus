"""Score determinístico (0-100) pra agentes e empresas."""
from sqlalchemy import text
from sqlalchemy.orm import Session


def calcular_score_agente(cpf: str, db: Session) -> float:
    score = 0.0

    r = db.execute(text("""
        SELECT COUNT(*) AS n FROM agentes_publicos a
          JOIN socios_empresa s ON s.cpf_socio = a.cpf
          JOIN contratos_publicos c ON c.cnpj_fornecedor = s.cnpj_empresa
         WHERE a.cpf = :cpf
           AND LOWER(c.orgao_contratante) LIKE '%' || LOWER(a.orgao) || '%'
    """), {"cpf": cpf}).fetchone()
    if r and r.n > 0:
        score += 40.0

    r = db.execute(text("""
        SELECT COUNT(*) AS n FROM socios_empresa s
          JOIN ceis ce ON ce.cnpj = s.cnpj_empresa
         WHERE s.cpf_socio = :cpf
    """), {"cpf": cpf}).fetchone()
    if r and r.n > 0:
        score += 20.0

    r = db.execute(text("""
        SELECT COUNT(*) AS n FROM socios_empresa s
          JOIN contratos_publicos c ON c.cnpj_fornecedor = s.cnpj_empresa
         WHERE s.cpf_socio = :cpf AND c.valor > 100000
    """), {"cpf": cpf}).fetchone()
    if r and r.n > 0:
        score += min(r.n * 10.0, 30.0)

    r = db.execute(text("""
        SELECT COUNT(*) AS n FROM socios_empresa s
          JOIN doacoes_eleitorais d ON d.cnpj_doador = s.cnpj_empresa
          JOIN contratos_publicos c ON c.cnpj_fornecedor = s.cnpj_empresa
         WHERE s.cpf_socio = :cpf
    """), {"cpf": cpf}).fetchone()
    if r and r.n > 0:
        score += 15.0

    r = db.execute(text("""
        SELECT remuneracao FROM agentes_publicos WHERE cpf = :cpf
    """), {"cpf": cpf}).fetchone()
    if r and r.remuneracao and r.remuneracao > 20000:
        score += 15.0

    return min(score, 100.0)


def calcular_score_empresa(cnpj: str, db: Session) -> float:
    score = 0.0

    r = db.execute(text("""
        SELECT COUNT(*) AS n FROM socios_empresa s
          JOIN agentes_publicos a ON a.cpf = s.cpf_socio
         WHERE s.cnpj_empresa = :cnpj
    """), {"cnpj": cnpj}).fetchone()
    if r and r.n > 0:
        score += 30.0

    r = db.execute(text("""
        SELECT COUNT(*) AS n FROM socios_empresa s
          JOIN agentes_publicos a ON a.cpf = s.cpf_socio
          JOIN contratos_publicos c ON c.cnpj_fornecedor = s.cnpj_empresa
         WHERE s.cnpj_empresa = :cnpj
           AND LOWER(c.orgao_contratante) LIKE '%' || LOWER(a.orgao) || '%'
    """), {"cnpj": cnpj}).fetchone()
    if r and r.n > 0:
        score += 25.0

    r = db.execute(text("""
        SELECT COUNT(*) AS n FROM ceis WHERE cnpj = :cnpj
    """), {"cnpj": cnpj}).fetchone()
    if r and r.n > 0:
        score += 20.0

    r = db.execute(text("""
        SELECT COUNT(*) AS n FROM doacoes_eleitorais d
          JOIN contratos_publicos c ON c.cnpj_fornecedor = d.cnpj_doador
         WHERE d.cnpj_doador = :cnpj
    """), {"cnpj": cnpj}).fetchone()
    if r and r.n > 0:
        score += 15.0

    r = db.execute(text("""
        SELECT COUNT(*) AS n FROM contratos_publicos
         WHERE cnpj_fornecedor = :cnpj AND valor > 1000000
    """), {"cnpj": cnpj}).fetchone()
    if r and r.n > 0:
        score += 10.0

    return min(score, 100.0)


def atualizar_todos_scores(db: Session) -> dict:
    from ..api.models import AgentePublico, Empresa

    n_ag = 0
    for a in db.query(AgentePublico).all():
        a.score_risco = calcular_score_agente(a.cpf, db)
        n_ag += 1

    n_emp = 0
    for e in db.query(Empresa).all():
        e.score_risco = calcular_score_empresa(e.cnpj, db)
        n_emp += 1

    db.commit()
    return {"agentes_atualizados": n_ag, "empresas_atualizadas": n_emp}
