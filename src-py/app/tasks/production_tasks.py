from app.core.celery_app import celery_app
from app.services.production_service import ProductionService
from app.services.sap_sync import SAPIntegrationService
from datetime import date, timedelta, datetime
import asyncio
from app.db.session import SessionLocal, async_session
from celery.schedules import crontab
from app.models.production_model import ProductionAppointment
from sqlalchemy import select

# --- UTILITÁRIOS ---

def run_async(coro):
    """Auxiliar para rodar funções assíncronas dentro do worker síncrono."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

# --- TAREFAS DE MÉTRICAS ---

@celery_app.task(name="task_daily_closing_yesterday")
def task_daily_closing_yesterday():
    """
    Consolida os indicadores (OEE, Disponibilidade) do dia anterior.
    Recomendado rodar via Celery Beat às 01:00 AM.
    """
    yesterday = date.today() - timedelta(days=1)
    
    async def _run():
        async with SessionLocal() as db:
            await ProductionService.consolidate_daily_metrics(db, yesterday)
            
    run_async(_run())
    return f"Fechamento realizado com sucesso para {yesterday}"

# --- TAREFA PRINCIPAL DE SINCRONISMO (SAP + MES) ---

@celery_app.task(name="process_sap_appointment", bind=True, max_retries=5)
def process_sap_appointment(self, appointment_data: dict, organization_id: int):
    """
    Processa dados do cockpit.
    1. Normaliza tempo e identidade.
    2. Evita duplicados já integrados.
    3. Salva no banco local (MES).
    4. Integra Produção e Paradas ao SAP.
    """
    async def _logic():
        from app import crud
        async with SessionLocal() as db:
            # 1. TRATAMENTO DE TEMPO (Garante compatibilidade com Postgres)
            raw_time = appointment_data.get('start_time') or appointment_data.get('timestamp')
            if not raw_time:
                return "Erro: Payload sem carimbo de tempo."

            # Converte para datetime e remove fuso horário (naive)
            dt_obj = datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
            dt_naive = dt_obj.replace(tzinfo=None)

            # 2. RESOLUÇÃO DE IDENTIDADE
            op_badge = str(appointment_data.get('operator_id') or appointment_data.get('operator_badge') or "0")
            vh_id = appointment_data.get('vehicle_id') or appointment_data.get('machine_id')

            # 3. CHECAGEM DE DUPLICIDADE INTELIGENTE
            stmt = select(ProductionAppointment).where(
                ProductionAppointment.operator_id == op_badge,
                ProductionAppointment.start_time == dt_naive,
                ProductionAppointment.vehicle_id == vh_id
            )
            exists = (await db.execute(stmt)).scalars().first()
            
            # Se já existe e JÁ FOI pro SAP, não fazemos nada.
            if exists and exists.sap_status == "SENT":
                return f"Item já sincronizado anteriormente (ID: {exists.id})"

            # 4. PERSISTÊNCIA NO BANCO LOCAL (MES)
            if not exists:
                new_entry = await crud.production.create_entry(db, obj_in=appointment_data)
                
            else:
                new_entry = exists # Tenta reprocessar o que já existe no banco mas falhou no SAP

            # Se for apenas um log de evento interno, paramos aqui
            if new_entry == "LOG_SAVED":
                return "Evento interno salvo na tabela de logs."

            # 5. LÓGICA DE FILTRAGEM SAP (O Ponto Crítico)
            is_stoppage = bool(appointment_data.get('stop_reason'))
            has_op = bool(appointment_data.get('op_number'))

            if is_stoppage or has_op:
            # Chama o SAPIntegrationService...
                pass

            is_internal_log = bool(appointment_data.get('event_type'))

            # Agora enviamos se tiver O.P. OU se for uma Parada (mesmo sem O.P.)
            if not is_internal_log and (has_op or is_stoppage):
                print(f"🏭 [SAP] Integrando {'PARADA' if is_stoppage else 'PRODUÇÃO'}...")
                
                sap_service = SAPIntegrationService(db, organization_id)
                
                try:
                    success = await sap_service.create_production_appointment(
                        appointment_data=appointment_data,
                        sap_resource_code=appointment_data.get('resource_code', '')
                    )

                    if success:
                        new_entry.sap_status = "SENT"
                        new_entry.sap_message = f"OK: {datetime.now().strftime('%H:%M:%S')}"
                    else:
                        new_entry.sap_status = "ERROR"
                        new_entry.sap_message = "Rejeitado pelo SAP Service Layer"
                
                except Exception as sap_err:
                    new_entry.sap_status = "RETRY"
                    new_entry.sap_message = str(sap_err)[:200]
                    await db.commit()
                    # Tenta novamente em 5 minutos se for erro de rede
                    raise self.retry(exc=sap_err, countdown=300)

            else:
                new_entry.sap_status = "NOT_REQUIRED"
                new_entry.sap_message = "Log interno / Status de máquina"

            await db.commit()
            return f"Finalizado: {new_entry.id} (SAP: {new_entry.sap_status})"

    return run_async(_logic())

@celery_app.task(name="tasks.daily_production_closing")
def daily_production_closing():
    """Tarefa automática que roda à meia-noite para fechar o dia anterior."""
    import asyncio
    yesterday = date.today() - timedelta(days=1)
    
    async def run_closing():
        async with async_session() as db:
            await ProductionService.consolidate_machine_metrics(db, yesterday)
            await ProductionService.consolidate_daily_metrics(db, yesterday)
    
    asyncio.run(run_closing())

# Configuração do Beat (No arquivo de configuração do Celery)
celery_app.conf.beat_schedule = {
    'close-production-every-night': {
        'task': 'tasks.daily_production_closing',
        'schedule': crontab(hour=0, minute=5), # 00:05 AM
    },
}