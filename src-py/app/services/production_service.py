from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from datetime import datetime
from typing import Optional, List, Dict

# Models
from app.models.production_model import ProductionLog, ProductionOrder, ProductionSession, ProductionTimeSlice
from app.models.vehicle_model import Vehicle, VehicleStatus
from app.models.user_model import User

# Schemas
from app.schemas.production_schema import ProductionEventCreate

class ProductionService:
    
    @staticmethod
    async def get_active_slice(db: AsyncSession, vehicle_id: int) -> Optional[ProductionTimeSlice]:
        """Busca a fatia de tempo que está aberta (sem end_time) para a máquina."""
        query = select(ProductionTimeSlice).where(
            ProductionTimeSlice.vehicle_id == vehicle_id,
            ProductionTimeSlice.end_time == None
        ).order_by(desc(ProductionTimeSlice.start_time))
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def close_current_slice(db: AsyncSession, vehicle_id: int, end_time: datetime = None):
        """Fecha a fatia de tempo atual, calculando a duração."""
        if not end_time:
            end_time = datetime.now()
            
        current_slice = await ProductionService.get_active_slice(db, vehicle_id)
        
        if current_slice:
            current_slice.end_time = end_time
            # Calcula duração em segundos
            delta = (end_time - current_slice.start_time).total_seconds()
            current_slice.duration_seconds = int(max(0, delta))
            db.add(current_slice)
            await db.commit() # Commit parcial para garantir integridade
            return current_slice
        return None

    @staticmethod
    async def open_new_slice(
        db: AsyncSession, 
        vehicle_id: int, 
        category: str, 
        reason: Optional[str] = None,
        session_id: Optional[int] = None,
        order_id: Optional[int] = None
    ) -> ProductionTimeSlice:
        """Abre uma nova fatia de tempo."""
        # Define flag de produtividade baseada na categoria
        is_productive = category == "PRODUCING"
        
        new_slice = ProductionTimeSlice(
            vehicle_id=vehicle_id,
            start_time=datetime.now(),
            category=category,
            reason=reason,
            is_productive=is_productive,
            session_id=session_id,
            order_id=order_id
        )
        db.add(new_slice)
        await db.commit()
        return new_slice

    @staticmethod
    async def handle_event(
        db: AsyncSession, 
        event: ProductionEventCreate
    ):
        """
        Processa um evento bruto vindo do Frontend e gerencia as fatias de tempo.
        """
        timestamp = datetime.now()
        
        # 1. Recuperar Entidades (Máquina, Operador, Ordem, Sessão)
        machine = await db.get(Vehicle, event.machine_id)
        if not machine:
            raise ValueError("Machine not found")

        # Buscar Sessão Ativa
        q_session = select(ProductionSession).where(
            ProductionSession.vehicle_id == machine.id,
            ProductionSession.end_time == None
        )
        session = (await db.execute(q_session)).scalars().first()
        
        # Buscar Ordem (Se código fornecido ou da sessão)
        order = None
        if event.order_code:
            q_order = select(ProductionOrder).where(ProductionOrder.code == event.order_code)
            order = (await db.execute(q_order)).scalars().first()
        elif session and session.production_order_id:
            order = await db.get(ProductionOrder, session.production_order_id)

        # 2. Registrar Log Bruto (Auditoria)
        # Buscar ID do operador pelo crachá
        q_user = select(User).where(User.email == event.operator_badge)
        user = (await db.execute(q_user)).scalars().first()
        
        log = ProductionLog(
            vehicle_id=machine.id,
            operator_id=user.id if user else None,
            order_id=order.id if order else None,
            session_id=session.id if session else None,
            event_type=event.event_type,
            new_status=event.new_status,
            previous_status=machine.status, # Status anterior da máquina
            reason=event.reason,
            details=event.details,
            timestamp=timestamp
        )
        db.add(log)

        # 3. Lógica de Fatias de Tempo (Time Slices)
        # Só mexe nas fatias se houver mudança de status ou início/fim de turno
        if event.new_status:
            # Mapeamento: Status Frontend -> Categoria TimeSlice (MES)
            status_map_category = {
                "EM OPERAÇÃO": "PRODUCING",
                "RUNNING": "PRODUCING",
                "IN_USE": "PRODUCING",
                
                "MANUTENÇÃO": "PLANNED_STOP", # Setup geralmente é planejado
                "SETUP": "PLANNED_STOP",
                
                "PARADA": "UNPLANNED_STOP", # Default para parada (refinar com 'reason')
                "STOPPED": "UNPLANNED_STOP",
                "PAUSED": "UNPLANNED_STOP",
                
                "IDLE": "IDLE",
                "AVAILABLE": "IDLE"
            }
            
            new_category = status_map_category.get(event.new_status.upper(), "UNKNOWN")
            
            # Refinamento por Motivo (Ex: Se motivo for 'Almoço', vira PLANNED_STOP)
            if event.reason and "ALMOÇO" in event.reason.upper():
                new_category = "PLANNED_STOP"
            
            # Fecha fatia anterior
            await ProductionService.close_current_slice(db, machine.id, timestamp)
            
            # Abre nova fatia
            await ProductionService.open_new_slice(
                db, 
                vehicle_id=machine.id, 
                category=new_category, 
                reason=event.reason,
                session_id=session.id if session else None,
                order_id=order.id if order else None
            )

            # 4. Atualizar Status "Visual" da Máquina (Para o Dashboard Tempo Real)
            # Mapa para o Enum do Banco (VehicleStatus)
            enum_map = {
                "PRODUCING": VehicleStatus.IN_USE,
                "PLANNED_STOP": VehicleStatus.MAINTENANCE,
                "UNPLANNED_STOP": VehicleStatus.AVAILABLE, # Ou MAINTENANCE, depende da regra de negócio
                "IDLE": VehicleStatus.AVAILABLE
            }
            # Se for parada não planejada (quebra), joga para Manutenção visualmente?
            if new_category == "UNPLANNED_STOP" and event.reason and "QUEBRA" in event.reason.upper():
                 machine.status = VehicleStatus.MAINTENANCE
            else:
                 machine.status = enum_map.get(new_category, VehicleStatus.AVAILABLE)
            
            db.add(machine)

        # 5. Atualizar Contadores da O.P.
        if event.event_type == 'COUNT' and order:
            order.produced_quantity += (event.quantity_good or 0)
            order.scrap_quantity += (event.quantity_scrap or 0)
            db.add(order)
            
            # Atualiza totais da sessão também
            if session:
                session.total_produced += (event.quantity_good or 0)
                session.total_scrap += (event.quantity_scrap or 0)
                db.add(session)

        await db.commit()
        return {"status": "processed", "new_category": status_map_category.get(event.new_status.upper()) if event.new_status else None}

    @staticmethod
    async def calculate_oee(db: AsyncSession, vehicle_id: int, start_date: datetime, end_date: datetime):
        """
        Calcula OEE baseado nas Fatias de Tempo (Time Slices).
        Disponibilidade = Tempo Produzindo / (Tempo Total - Paradas Planejadas)
        """
        # Buscar todas as fatias no período
        query = select(ProductionTimeSlice).where(
            ProductionTimeSlice.vehicle_id == vehicle_id,
            ProductionTimeSlice.start_time >= start_date,
            ProductionTimeSlice.start_time <= end_date,
            ProductionTimeSlice.duration_seconds > 0 # Só fatias fechadas
        )
        slices = (await db.execute(query)).scalars().all()
        
        total_time = sum(s.duration_seconds for s in slices)
        planned_stop_time = sum(s.duration_seconds for s in slices if s.category == "PLANNED_STOP")
        producing_time = sum(s.duration_seconds for s in slices if s.category == "PRODUCING")
        
        # 1. Disponibilidade
        operating_time = total_time - planned_stop_time
        availability = (producing_time / operating_time) if operating_time > 0 else 0
        
        # 2. Performance e Qualidade requerem dados da O.P. (Quantidade Teórica vs Real)
        # Simplificação: Performance = 100% se não tiver cadastro de ciclo padrão
        performance = 1.0 
        quality = 1.0
        
        return {
            "oee_percentage": round(availability * performance * quality * 100, 2),
            "availability": round(availability * 100, 2),
            "performance": round(performance * 100, 2),
            "quality": round(quality * 100, 2),
            "metrics": {
                "total_time_min": total_time / 60,
                "planned_stop_min": planned_stop_time / 60,
                "producing_min": producing_time / 60
            }
        }