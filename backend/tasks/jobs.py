"""Tasks Celery do Hórus — agendadas via celery beat."""
from ..analytics.score import atualizar_todos_scores
from ..api.database import SessionLocal
from ..ingestao_lib.cgu import ingerir_ceis, ingerir_contratos_sancionados
from .celery_app import celery_app


@celery_app.task(name="backend.tasks.jobs.reingere_ceis")
def reingere_ceis(max_paginas: int = 30) -> dict:
    """Re-ingere CEIS e contratos das sancionadas. Roda semanalmente."""
    with SessionLocal() as db:
        r1 = ingerir_ceis(db, max_paginas=max_paginas)
        r2 = ingerir_contratos_sancionados(db, max_paginas_por_empresa=2)
        return {"ceis": r1, "contratos": r2}


@celery_app.task(name="backend.tasks.jobs.recalcular_scores")
def recalcular_scores() -> dict:
    """Recalcula score de risco de todos os agentes e empresas."""
    with SessionLocal() as db:
        return atualizar_todos_scores(db)
