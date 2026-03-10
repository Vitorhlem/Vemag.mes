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

# ============================================================================
# TAREFA 1: APONTAMENTO (ESCRITA NO SAP E BANCO LOCAL)
# ============================================================================
@celery_app.task(name="process_sap_appointment", bind=True, max_retries=3)
def process_sap_appointment(self, appointment_data: dict, organization_id: int):
    async def _logic():
        async with SessionLocal() as db:
            sap_service = SAPIntegrationService(db, organization_id)
            print(f"🏭 [CELERY] Processando apontamento SAP para OP {appointment_data.get('op_number', 'N/A')}...")
            
            # 1. TRATAMENTO DE TEMPO
            def parse_date(dt_val):
                if not dt_val: return None
                if isinstance(dt_val, datetime): return dt_val.replace(tzinfo=None)
                if isinstance(dt_val, str): return datetime.fromisoformat(dt_val.replace('Z', '+00:00')).replace(tzinfo=None)
                return None

            start_t = parse_date(appointment_data.get('start_time') or appointment_data.get('timestamp'))
            end_t = parse_date(appointment_data.get('end_time'))
            
            op_badge = str(appointment_data.get('operator_badge') or appointment_data.get('operator_id') or "0")
            m_id = appointment_data.get('machine_id')

            # 2. CHECAGEM DE DUPLICIDADE (Usando o novo campo 'operator_badge')
            stmt = select(ProductionAppointment).where(
                ProductionAppointment.operator_badge == op_badge,
                ProductionAppointment.start_time == start_t,
                ProductionAppointment.machine_id == m_id
            )
            existing_appt = (await db.execute(stmt)).scalars().first()
            
            if existing_appt and existing_appt.sap_status == "SENT":
                return f"Apontamento já sincronizado no SAP (ID: {existing_appt.id})"

            # 3. LÓGICA DE DETECÇÃO DE EVENTOS
            is_internal_log = bool(appointment_data.get('event_type'))
            op_number_raw = str(appointment_data.get('op_number', ''))
            is_os = op_number_raw.startswith("OS-")
            is_stop_reason = bool(appointment_data.get('stop_reason'))
            is_setup_desc = "setup" in str(appointment_data.get('stop_description', '')).lower()
            is_stop = is_stop_reason or is_setup_desc
            has_op = bool(op_number_raw)

            # 4. ENVIO PARA O SAP (Só envia se tiver OP ou for parada)
            success = False
            sap_msg = "Log interno salvo apenas no MES"
            
            if not is_internal_log and (has_op or is_stop):
                try:
                    success = await sap_service.create_production_appointment(
                        appointment_data=appointment_data,
                        sap_resource_code=appointment_data.get('resource_code', '')
                    )
                    sap_msg = "Sincronizado via Celery" if success else "Rejeitado pelo SAP"
                except Exception as sap_err:
                    sap_msg = f"Erro de rede: {str(sap_err)}"
                    print(f"❌ [CELERY] Falha na integração SAP: {sap_err}")

            # 5. PREPARAR CAMPOS ESPELHADOS PARA O BANCO LOCAL
            if is_os and '-' in op_number_raw:
                try: final_doc_num = op_number_raw.split('-')[1]
                except: final_doc_num = op_number_raw
            else:
                final_doc_num = op_number_raw

            u_tipo_doc = "2" if (is_stop or is_os) else "1"
            u_servico = str(appointment_data.get('item_code', '')) if is_os else None
            is_setup_val = "S" if is_setup_desc else "N"
            is_apto_parada = "S" if (is_stop_reason or is_setup_val == "S") else "N"
            
            if is_stop:
                posicao_final = ""
                operacao_final = ""
            else:
                posicao_final = str(appointment_data.get('position', ''))
                operacao_final = str(appointment_data.get('operation', ''))
                
            raw_op_id = str(appointment_data.get('operator_id', '0'))
            clean_op_id = raw_op_id.lstrip('0')[:-1] if len(raw_op_id) > 1 and raw_op_id.isdigit() else raw_op_id

            # Se já existe (mas falhou antes), apenas atualiza o status. Se não, cria um novo.
            if not existing_appt:
                existing_appt = ProductionAppointment(
                    machine_id=m_id,
                    operator_badge=op_badge,
                    appointment_type="STOP" if is_stop else "PRODUCTION",
                    start_time=start_t,
                    end_time=end_t or start_t, 
                    
                    # Campos SAP
                    sap_doc_num=final_doc_num,
                    sap_position=posicao_final,
                    sap_operation_code=operacao_final,
                    sap_operation_desc=appointment_data.get('operation_desc', ''),
                    sap_service_desc=appointment_data.get('part_description', ''),
                    sap_operator_name=appointment_data.get('operator_name', ''),
                    operator_id=clean_op_id, 
                    sap_resource_code=appointment_data.get('resource_code', ''),
                    sap_resource_name=appointment_data.get('resource_name', ''),
                    sap_data_source="I",
                    sap_doc_type=u_tipo_doc,
                    sap_origin="S",
                    sap_service_code=u_servico,
                    sap_stop_reason_code=appointment_data.get('stop_reason', ""),
                    sap_stop_reason_desc=appointment_data.get('stop_description', ""),
                    sap_is_setup=is_setup_val,
                    sap_stoppage_apt=is_apto_parada,
                    
                    sap_status="SENT" if success else ("ERROR" if not is_internal_log else "NOT_REQUIRED"),
                    sap_message=sap_msg
                )
                db.add(existing_appt)
            else:
                existing_appt.sap_status = "SENT" if success else "ERROR"
                existing_appt.sap_message = sap_msg

            await db.commit()
            print(f"✅ [CELERY] Apontamento local espelhado salvo. ID: {existing_appt.id}")

            # 6. DISPARA NOTIFICAÇÃO PUSH SE FOR MANUTENÇÃO (Cód 21 ou 34)
            reason = str(appointment_data.get('stop_reason'))
            if reason in ['21', '34']:
                from app.services.fcm_service import enviar_push_lista
                from app.models.user_model import User, UserRole
                from app.models.machine_model import Machine
                machine = await db.get(Machine, m_id)
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