# Localização: src-py/app/crud/crud_production.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.production_model import ProductionAppointment, ProductionLog
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
    
    async def create_entry(self, db, *, obj_in: dict):
        # Normalização de tempo
        raw_time = obj_in.get("start_time") or obj_in.get("timestamp") or datetime.now().isoformat()
        dt_naive = datetime.fromisoformat(raw_time.replace('Z', '+00:00')).replace(tzinfo=None)

        # DECISÃO: É um log de sistema ou um apontamento de fábrica?
        is_event = "event_type" in obj_in
        
        if is_event:
            # GAVETA DE LOGS
            db_log = ProductionLog(
                vehicle_id=obj_in.get("machine_id") or obj_in.get("vehicle_id"),
                operator_id=str(obj_in.get("operator_badge") or obj_in.get("operator_id") or ""),
                event_type=obj_in.get("event_type"),
                timestamp=dt_naive,
                reason=obj_in.get("reason"),
                details=str(obj_in.get("reason") or obj_in.get("new_status") or "")
            )
            db.add(db_log)
            await db.commit()
            return "LOG_SAVED"

        else:
            # GAVETA DE APONTAMENTOS (Produção/Parada/OS)
            db_obj = ProductionAppointment(
                vehicle_id=obj_in.get("vehicle_id") or obj_in.get("machine_id"),
                operator_id=str(obj_in.get("operator_id") or obj_in.get("operator_badge")),
                op_number=obj_in.get("op_number") or "",
                position=obj_in.get("position") or "",
                operation_code=obj_in.get("operation") or "",
                start_time=dt_naive,
                end_time=datetime.fromisoformat(obj_in.get("end_time", raw_time).replace('Z', '+00:00')).replace(tzinfo=None),
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