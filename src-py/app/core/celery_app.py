# Localização: src-py/app/core/celery_app.py
from celery import Celery
import os

celery_app = Celery(
    "trucar_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    # --- ADICIONE ESTA LINHA ABAIXO ---
    include=[
        "app.tasks.andon_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.production_tasks" 
    ]
    
    # ---------------------------------
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
)