"""Celery app — broker Redis em localhost:6380."""
import os

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")

celery_app = Celery(
    "horus",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.tasks.jobs"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=False,
    task_track_started=True,
)

# Schedule: re-ingere CEIS toda segunda 03:00 (3h da manhã).
celery_app.conf.beat_schedule = {
    "reingere-ceis-semanal": {
        "task": "backend.tasks.jobs.reingere_ceis",
        "schedule": crontab(hour=3, minute=0, day_of_week="mon"),
        "args": (30,),
    },
    "recalcula-scores-diario": {
        "task": "backend.tasks.jobs.recalcular_scores",
        "schedule": crontab(hour=4, minute=0),
    },
}
