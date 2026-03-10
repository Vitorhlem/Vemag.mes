# Localização: src-py/app/crud/crud_production.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.production_model import ProductionAppointment, ProductionLog
from sqlalchemy import select
from app.models.user_model import User  # <--- IMPORT NOVO
from datetime import datetime

class CRUDProduction:
    async def create_appointment(self, db: AsyncSession, *, obj_in: dict) -> ProductionAppointment:
        # 1. Tenta pegar start_time, se não houver, tenta timestamp, se não houver, usa 'now'
        raw_start = obj_in.get("start_time") or obj_in.get("timestamp") or datetime.now().isoformat()
        raw_end = obj_in.get("end_time") or raw_start # Se for um evento pontual, start = end

        # 2. Converte para objeto datetime seguro (Naive para o Postgres)
        start_dt = datetime.fromisoformat(raw_start.replace('Z', '+00:00')).replace(tzinfo=None)
        end_dt = datetime.fromisoformat(raw_end.replace('Z', '+00:00')).replace(tzinfo=None)

        db_obj = ProductionAppointment(
            machine_id=obj_in.get("machine_id") or obj_in.get("machine_id"),
            operator_id=str(obj_in.get("operator_id") or obj_in.get("operator_badge") or "0"),
            op_number=obj_in.get("op_number", "N/A"),
            position=obj_in.get("position", "000"),
            operation_code=obj_in.get("operation", "000"),
            start_time=start_dt,
            end_time=end_dt,
            appointment_type=obj_in.get("appointment_type") or obj_in.get("event_type", "PRODUCTION"),
            sap_status="PENDING"
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def create_entry(self, db: AsyncSession, *, obj_in: dict):
        
        # 1. Função auxiliar blindada para converter datas
        def parse_safe_date(dt_val):
            if not dt_val:
                return None
            # Se já for um objeto datetime (vindo do FastAPI), apenas remove o fuso horário
            if isinstance(dt_val, datetime):
                return dt_val.replace(tzinfo=None)
            # Se for uma string (vindo do modo offline/JSON), converte tratando o 'Z'
            if isinstance(dt_val, str):
                try:
                    return datetime.fromisoformat(dt_val.replace('Z', '+00:00')).replace(tzinfo=None)
                except ValueError:
                    return None
            return None

        # 2. Extração segura das datas usando a função auxiliar
        raw_time = obj_in.get("start_time") or obj_in.get("timestamp")
        dt_naive = parse_safe_date(raw_time)
        
        end_time_raw = obj_in.get("end_time")
        # Se não houver end_time, usamos o start_time/timestamp como fallback
        end_naive = parse_safe_date(end_time_raw) or dt_naive

        # DECISÃO: É um log de sistema ou um apontamento de fábrica?
        is_event = "event_type" in obj_in
        
        if is_event:
            # ==========================================
            # GAVETA DE LOGS (ProductionLog)
            # ==========================================
            badge = str(obj_in.get("operator_badge") or obj_in.get("operator_id") or "")
            
            # 1. Tenta encontrar o nome do usuário para registro
            user_id_found = None
            if badge: 
                from app.models.user_model import User 
                from sqlalchemy import select, or_
                # Procura por crachá, ou por email/nome se o front enviar errado
                stmt = select(User).where(or_(User.employee_id == badge, User.full_name == badge))
                result = await db.execute(stmt)
                user = result.scalars().first()
                if user:
                    user_id_found = user.id

            db_obj = ProductionLog(
                machine_id=obj_in.get("machine_id"),
                operator_id=user_id_found,
                operator_badge=badge,
                operator_name=obj_in.get("operator_name"),
                event_type=obj_in.get("event_type", "SYSTEM"),
                timestamp=dt_naive,      
                new_status=obj_in.get("new_status") or obj_in.get("status"),
                reason=obj_in.get("reason"),
                details=obj_in.get("details") # 👇 DE VOLTA AQUI
            )
            db.add(db_obj)
            await db.commit()
            return "LOG_SAVED"

        else:
            # ==========================================
            # GAVETA DE APONTAMENTOS (ProductionAppointment - Espelho SAP)
            # ==========================================
            
            # A. Detecção do tipo de ordem e evento
            op_number_raw = str(obj_in.get('op_number', ''))
            is_os = op_number_raw.startswith("OS-")
            is_stop_reason = bool(obj_in.get('stop_reason'))
            is_setup_desc = "setup" in str(obj_in.get('stop_description', '')).lower()
            is_stop = is_stop_reason or is_setup_desc

            # B. Limpeza do número do Documento (Tira o "OS-" e o sufixo de linha)
            if is_os and '-' in op_number_raw:
                try: 
                    final_doc_num = op_number_raw.split('-')[1]
                except: 
                    final_doc_num = op_number_raw
            else:
                final_doc_num = op_number_raw

            # C. Regras de Negócio do SAP
            u_tipo_doc = "2" if (is_stop or is_os) else "1"
            u_servico = str(obj_in.get('item_code', '')) if is_os else None
            is_setup_val = "S" if is_setup_desc else "N"
            is_apto_parada = "S" if (is_stop_reason or is_setup_val == "S") else "N"
            
            if is_stop:
                posicao_final = ""
                operacao_final = ""
            else:
                posicao_final = str(obj_in.get('position', ''))
                operacao_final = str(obj_in.get('operation', ''))

            # D. Limpeza do Operador para o SAP
            raw_op_id = str(obj_in.get('operator_id', '0'))
            clean_op_id = raw_op_id.lstrip('0')[:-1] if len(raw_op_id) > 1 and raw_op_id.isdigit() else raw_op_id

            # E. Criação do Objeto exato conforme o Modelo
            db_obj = ProductionAppointment(
                machine_id=obj_in.get("machine_id"),
                operator_badge=str(obj_in.get("operator_badge") or obj_in.get("operator_id") or "0"),
                appointment_type="STOP" if is_stop else "PRODUCTION",
                start_time=dt_naive,     
                end_time=end_naive,       
                
                # Campos Espelho SAP (Exatamente os do seu modelo)
                sap_doc_num=final_doc_num,
                sap_position=posicao_final,
                sap_operation_code=operacao_final,
                sap_operation_desc=obj_in.get("operation_desc"),
                sap_service_desc=obj_in.get("part_description"),
                sap_operator_name=obj_in.get("operator_name"),
                operator_id=clean_op_id,  # Seu modelo usa 'operator_id' aqui
                sap_resource_code=obj_in.get("resource_code"),
                sap_resource_name=obj_in.get("resource_name"),
                sap_data_source="I",
                sap_doc_type=u_tipo_doc,
                sap_origin="S",
                sap_service_code=u_servico,
                sap_stop_reason_code=obj_in.get("stop_reason"),
                sap_stop_reason_desc=obj_in.get("stop_description"),
                sap_is_setup=is_setup_val,
                sap_stoppage_apt=is_apto_parada,
                
                # Status e Quantidades
                sap_status=obj_in.get("sap_status", "PENDING"),
                sap_message=obj_in.get("sap_message"),
                target_qty=float(obj_in.get("target_qty", 0.0))
            )
            
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj

production = CRUDProduction()