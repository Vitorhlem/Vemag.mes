# Arquivo: src-py/app/tasks/production_tasks.py
from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.production_service import ProductionService
from datetime import date, timedelta
import asyncio

@celery_app.task
def task_daily_closing_yesterday():
    """
    Tarefa do Celery para fechar o dia anterior.
    Pode ser agendada para rodar todo dia às 01:00 da manhã.
    """
    yesterday = date.today() - timedelta(days=1)
    
    async def run_async():
        async with AsyncSessionLocal() as db:
            await ProductionService.consolidate_daily_metrics(db, yesterday)
            
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_async())
    return f"Fechamento realizado para {yesterday}"