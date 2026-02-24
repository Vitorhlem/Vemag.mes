from app.core.celery_app import celery_app
from app.services.production_service import ProductionService
from app.services.sap_sync import SAPIntegrationService
from datetime import date, timedelta, datetime
import asyncio
from app.db.session import SessionLocal, async_session
from celery.schedules import crontab
from app.models.production_model import ProductionAppointment
from sqlalchemy import select
from app.core.websocket_manager import manager
import requests

# --- UTILITÁRIOS ---

def run_async(coro):
    """
    Executa uma corotina de forma síncrona, garantindo que a thread
    (como as threads background do Celery) tenha um event loop válido.
    """
    try:
        # Tenta pegar o loop atual da thread
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Se falhar (não tem loop na thread), cria um novo e define como padrão
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(coro)

# --- TAREFAS DE MÉTRICAS ---

@celery_app.task(name="task_daily_closing_yesterday")
def task_daily_closing_yesterday():
    """
    Roda todo dia de madrugada para calcular a eficiência, paradas e tempo
    de todos os operadores e máquinas referentes ao dia que acabou de terminar.
    """
    # Como a task roda de madrugada (ex: 00:05 do dia 20), os dados que queremos são do dia 19
    yesterday = date.today() - timedelta(days=1)
    
    async def _run_closing():
        async with SessionLocal() as db:
            print(f"🌙 [CELERY] Iniciando fechamento diário para o dia {yesterday}...")
            
            try:
                # 1. Consolida as métricas das MÁQUINAS 
                machines_processed = await ProductionService.consolidate_machine_metrics(db, target_date)
                print(f"✅ [CELERY] Fechamento de MÁQUINAS concluído: {machines_processed} processadas.")

                # 2. Consolida as métricas dos OPERADORES 
                users_processed = await ProductionService.consolidate_daily_metrics(db, target_date)
                print(f"✅ [CELERY] Fechamento de OPERADORES concluído: {users_processed} processados.")
                
                # 🚀 NOVIDADE: Avisa os painéis (WebSocket) para darem F5 sozinhos
                import httpx
                payload = {
                    "type": "DAILY_CLOSING_COMPLETED",
                    "message": "Fechamento diário concluído!"
                }
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post("http://127.0.0.1:8000/api/v1/production/internal/broadcast", json=payload)
                    print("📣 [CELERY] Telas avisadas para sincronizar.")
                except Exception as e:
                    print(f"⚠️ [CELERY] Aviso: Falha ao notificar o painel: {e}")

            except Exception as e:
                print(f"❌ [CELERY] Erro Crítico durante o fechamento diário: {str(e)}")
                import traceback
                traceback.print_exc()

    # Usamos a nossa função segura 'run_async' em vez de asyncio.run()
    run_async(_run_closing())
    
    return f"Fechamento do dia {yesterday} concluído."

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

            # ✅ CORREÇÃO: Verifica se é string ou se já é um objeto datetime
            if isinstance(raw_time, datetime):
                dt_naive = raw_time.replace(tzinfo=None)
            elif isinstance(raw_time, str):
                dt_naive = datetime.fromisoformat(raw_time.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                return "Erro: Tipo de data não suportado."

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

# Configuração do Beat (No arquivo de configuração do Celery)
celery_app.conf.beat_schedule = {
    'fechamento-diario-meia-noite': {
        'task': 'task_daily_closing_yesterday',
        # Executa todo dia às 00:05 (Dá 5 minutos de margem para os últimos apontamentos do dia entrarem)
        'schedule': crontab(hour=0, minute=5), 
    },
}

# ============================================================================
# TAREFA 1: APONTAMENTO (ESCRITA NO SAP E BANCO LOCAL)
# ============================================================================
@celery_app.task(name="process_sap_appointment", bind=True, max_retries=3)
def process_sap_appointment(self, appointment_data: dict, organization_id: int):
    async def _logic():
        async with SessionLocal() as db:
            sap_service = SAPIntegrationService(db, organization_id)
            print(f"🏭 [CELERY] Iniciando integração SAP para OP {appointment_data.get('op_number')}...")
            
            # 1. Tenta enviar para o SAP
            success = False
            sap_msg = ""
            try:
                success = await sap_service.create_production_appointment(
                    appointment_data=appointment_data,
                    sap_resource_code=appointment_data.get('resource_code', '')
                )
                sap_msg = "Sincronizado via Celery" if success else "Rejeitado pelo SAP"
            except Exception as sap_err:
                sap_msg = f"Erro de rede: {str(sap_err)}"
                print(f"❌ [CELERY] Falha na integração SAP: {sap_err}")
            
            # 2. Salva o Apontamento no MES Local
            appt_type = "STOP" if appointment_data.get('stop_reason') else "PRODUCTION"
            
            # ✅ CORREÇÃO: Função inteligente para lidar com Data ou String
            def parse_date(dt_val):
                if not dt_val:
                    return None
                if isinstance(dt_val, datetime):
                    return dt_val.replace(tzinfo=None)
                if isinstance(dt_val, str):
                    return datetime.fromisoformat(dt_val.replace('Z', '+00:00')).replace(tzinfo=None)
                return None

            start_t = parse_date(appointment_data.get('start_time'))
            end_t = parse_date(appointment_data.get('end_time'))

            new_appointment = ProductionAppointment(
                op_number=appointment_data.get('op_number'),
                operator_id=str(appointment_data.get('operator_id', '0')),
                vehicle_id=appointment_data.get('vehicle_id'),
                start_time=start_t,
                end_time=end_t,
                position=appointment_data.get('position'),
                operation_code=appointment_data.get('operation'),
                appointment_type=appt_type,
                stop_reason=appointment_data.get('stop_reason'),
                sap_status="SENT" if success else "ERROR",
                sap_message=sap_msg
            )
            db.add(new_appointment)
            await db.commit()
            print(f"✅ [CELERY] Apontamento local salvo. ID: {new_appointment.id}")

            # 3. Dispara Push Notification se for Manutenção (Cód 21)
            reason = str(appointment_data.get('stop_reason'))
            if reason in ['21', '34']:
                from app.services.fcm_service import enviar_push_lista
                from app.models.user_model import User, UserRole
                from app.models.vehicle_model import Vehicle
                machine = await db.get(Vehicle, appointment_data.get('vehicle_id'))
                m_name = f"{machine.brand} {machine.model}" if machine else "Máquina"
                
                query = select(User.device_token).where(
                    User.organization_id == organization_id, 
                    User.role.in_([UserRole.MAINTENANCE, UserRole.MANAGER, UserRole.ADMIN]), 
                    User.device_token.isnot(None)
                )
                tokens = (await db.execute(query)).scalars().all()
                if tokens:
                    msg = f"{m_name} parou.\nMotivo: Manutenção (Cód {reason})"
                    enviar_push_lista(list(tokens), "🛑 MÁQUINA PARADA", msg, {"tipo": "manutencao"})

    return run_async(_logic())
# ============================================================================
# TAREFA 2: BUSCA DE TODAS AS OPs ABERTAS
# ============================================================================
@celery_app.task(name="task_fetch_open_orders")
def task_fetch_open_orders(machine_id: int):
    async def _logic():
        async with SessionLocal() as db:
            sap_service = SAPIntegrationService(db, organization_id=1)
            ops = await sap_service.get_released_production_orders()
            oss = await sap_service.get_open_service_orders()
            return ops + oss # Retorna a lista para fora da função async

    all_orders = run_async(_logic())
    
    payload = {
        "type": "SAP_OPEN_ORDERS",
        "machine_id": machine_id,
        "data": all_orders
    }
    
    # 🚀 Disparo Síncrono e na rede correta do Docker (backend:8000)
    try:
        requests.post("http://192.168.0.22:8000/api/v1/production/internal/broadcast", json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Erro ao avisar o FastAPI: {e}")

    return f"Busca de OPs concluída para Máquina {machine_id}"

# ============================================================================
# TAREFA 3: BUSCA DETALHES DE UMA O.P. ESPECÍFICA (QR Code)
# ============================================================================
@celery_app.task(name="task_fetch_order_details")
def task_fetch_order_details(code: str, machine_id: int):
    async def _logic():
        async with SessionLocal() as db:
            sap_service = SAPIntegrationService(db, organization_id=1)
            return await sap_service.get_production_order_by_code(code)

    sap_data = run_async(_logic())
    
    payload = {
        "type": "SAP_ORDER_DATA", # 👈 Nome da mensagem corrigida para o frontend ler
        "code": code,
        "machine_id": machine_id,
        "data": sap_data
    }
    
    try:
        requests.post("http://192.168.0.22:8000/api/v1/production/internal/broadcast", json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Erro ao avisar o FastAPI: {e}")

    return f"Busca de OP {code} concluída"