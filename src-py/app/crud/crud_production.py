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
            vehicle_id=obj_in.get("vehicle_id") or obj_in.get("machine_id"),
            operator_id=str(obj_in.get("operator_id") or obj_in.get("operator_badge") or "0"),
            op_number=obj_in.get("op_number", "N/A"),
            position=obj_in.get("position", "000"),
            operation_code=obj_in.get("operation", "000"),
            start_time=start_dt,
            end_time=end_dt,
            produced_qty=float(obj_in.get("produced_qty", 0.0)),
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
            # GAVETA DE LOGS (ProductionLog)
            badge = str(obj_in.get("operator_badge") or obj_in.get("operator_id") or "")
            
            # 1. Tenta encontrar o nome do usuário para registro
            user_id_found = None
            if badge and badge.isdigit():
                stmt = select(User).where(User.employee_id == badge)
                result = await db.execute(stmt)
                user = result.scalars().first()
                if user:
                    user_id_found = user.id

            # 🚀 CORREÇÃO AQUI: Removemos os campos que não existem na tabela de log (op_number, position, end_time, etc)
            db_obj = ProductionLog(
                vehicle_id=obj_in.get("vehicle_id") or obj_in.get("machine_id"),
                
                # operator_id na tabela Log é Integer (Chave Estrangeira). 
                # operator_badge é String (Histórico). 
                operator_id=user_id_found,
                operator_badge=badge,
                operator_name=obj_in.get("operator_name"),
                
                event_type=obj_in.get("event_type", "SYSTEM"),
                timestamp=dt_naive,      # ✅ TRATADO
                new_status=obj_in.get("new_status") or obj_in.get("status"),
                reason=obj_in.get("reason"),
                details=obj_in.get("details")
            )
            db.add(db_obj)
            await db.commit()
            return "LOG_SAVED"

        else:
            # GAVETA DE APONTAMENTOS (ProductionAppointment)
            db_obj = ProductionAppointment(
                vehicle_id=obj_in.get("vehicle_id") or obj_in.get("machine_id"),
                operator_id=str(obj_in.get("operator_id") or obj_in.get("operator_badge") or "0"),
                op_number=str(obj_in.get("op_number") or ""),
                position=str(obj_in.get("position") or ""),
                operation_code=str(obj_in.get("operation") or ""),
                start_time=dt_naive,     # ✅ TRATADO
                end_time=end_naive,       # ✅ CORREÇÃO: Usando a variável tratada aqui!
                produced_qty=float(obj_in.get("produced_qty", 0.0)),
                appointment_type="STOP" if obj_in.get("stop_reason") else "PRODUCTION",
                stop_reason=obj_in.get("stop_reason"),
                sap_status="PENDING"
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj

production = CRUDProduction()