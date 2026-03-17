from celery import Celery
from celery.schedules import crontab
import os

celery_app = Celery(
    "mes_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=[
        "app.tasks.andon_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.production_tasks" 
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
)


celery_app.conf.beat_schedule = {
    "fechamento-diario-automatico": {
        "task": "task_daily_closing_yesterday",
        "schedule": crontab(hour=0, minute=5), 
    }
}