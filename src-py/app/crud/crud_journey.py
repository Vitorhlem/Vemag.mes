from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Tuple, Union, Dict, Any, Optional
from sqlalchemy import desc 

from datetime import datetime, date, timedelta

from app.crud.base import CRUDBase
from app.models.journey_model import Journey
from app.models.vehicle_model import Vehicle, VehicleStatus
from app.models.user_model import User, UserRole
from app.schemas.journey_schema import JourneyCreate, JourneyUpdate
from app.models.implement_model import Implement, ImplementStatus
from app.models.alert_model import Alert, AlertLevel

class VehicleNotAvailableError(Exception):
    pass

class CRUDJourney(CRUDBase[Journey, JourneyCreate, JourneyUpdate]):

    async def create_journey(
        self, db: AsyncSession, *, journey_in: JourneyCreate, driver_id: int, organization_id: int
    ) -> Journey:
        # Lógica de Implemento
        if journey_in.implement_id:
            implement = await db.get(Implement, journey_in.implement_id)
            if not implement or implement.organization_id != organization_id:
                raise ValueError("Implemento não encontrado.")
            if implement.status != ImplementStatus.AVAILABLE:
                raise VehicleNotAvailableError(f"O implemento {implement.name} não está disponível.")
            implement.status = ImplementStatus.IN_USE
            db.add(implement)
        
        # Validação de Veículo
        if not journey_in.vehicle_id:
            raise ValueError("O ID da máquina é obrigatório.")
            
        vehicle = await db.get(Vehicle, journey_in.vehicle_id)
        if not vehicle or vehicle.organization_id != organization_id:
            raise ValueError("Maquinário não encontrado.")
            
        if vehicle.status != VehicleStatus.AVAILABLE:
            raise VehicleNotAvailableError(f"A máquina {vehicle.brand} {vehicle.model} não está disponível.")

        journey_data = journey_in.model_dump(exclude_unset=True)
        
        # Garante consistência com o valor atual da máquina
        if journey_in.start_engine_hours is not None:
             current = vehicle.current_engine_hours or 0
             if journey_in.start_engine_hours < current:
                 journey_data['start_engine_hours'] = current
        else:
             journey_data['start_engine_hours'] = vehicle.current_engine_hours or 0

        # Cria a Jornada
        db_journey = Journey(
            **journey_data,
            driver_id=driver_id,
            organization_id=organization_id,
            is_active=True,
            start_time=datetime.utcnow()
        )
        db.add(db_journey)
        
        # Atualiza status da máquina
        vehicle.status = VehicleStatus.IN_USE
        db.add(vehicle)

        await db.commit()
        await db.refresh(db_journey, ['vehicle', 'driver', 'implement'])
        return db_journey

    async def end_journey(
        self, db: AsyncSession, *, db_journey: Journey, journey_in: JourneyUpdate
    ) -> Tuple[Journey, Vehicle]:
        """Finaliza operação e atualiza horímetro da máquina."""
        
        db_journey.end_time = datetime.utcnow()
        db_journey.is_active = False
        
        if journey_in.end_engine_hours is not None:
            db_journey.end_engine_hours = journey_in.end_engine_hours
        if journey_in.end_mileage is not None:
            db_journey.end_mileage = journey_in.end_mileage
        
        db.add(db_journey)

        updated_vehicle = None
        if db_journey.vehicle_id:
            vehicle = await db.get(Vehicle, db_journey.vehicle_id)
            if vehicle:
                vehicle.status = VehicleStatus.AVAILABLE
                
                # --- Atualização do Horímetro/KM ---
                if journey_in.end_engine_hours is not None:
                    current = vehicle.current_engine_hours or 0
                    if journey_in.end_engine_hours >= current:
                        vehicle.current_engine_hours = journey_in.end_engine_hours
                
                elif journey_in.end_mileage is not None:
                    current_km = vehicle.current_km or 0
                    if journey_in.end_mileage >= current_km:
                        vehicle.current_km = journey_in.end_mileage

                # Verifica Preventiva
                limit = vehicle.next_maintenance_km
                current = vehicle.current_engine_hours or 0
                
                if limit and current >= limit:
                    alert = Alert(
                        message=f"Manutenção Vencida: Máquina atingiu {current}h (Limite: {limit}h)",
                        level=AlertLevel.WARNING,
                        organization_id=vehicle.organization_id,
                        vehicle_id=vehicle.id,
                        driver_id=db_journey.driver_id
                    )
                    db.add(alert)

                db.add(vehicle) 
                updated_vehicle = vehicle

        if db_journey.implement_id:
            implement = await db.get(Implement, db_journey.implement_id)
            if implement:
                implement.status = ImplementStatus.AVAILABLE
                db.add(implement)

        await db.commit()
        await db.refresh(db_journey)
        if updated_vehicle:
            await db.refresh(updated_vehicle)
        
        return db_journey, updated_vehicle

    # --- MÉTODO RESTAURADO (CRUCIAL PARA O ERRO ATUAL) ---
    async def get_active_journey_by_driver(self, db: AsyncSession, *, driver_id: int, organization_id: int) -> Optional[Journey]:
        stmt = select(Journey).where(
            Journey.driver_id == driver_id,
            Journey.organization_id == organization_id,
            Journey.is_active == True
        )
        # Opcional: carregar relacionamentos se necessário
        stmt = stmt.options(
            selectinload(Journey.vehicle),
            selectinload(Journey.implement)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    # --- MÉTODO DE LISTAGEM COMPLETA ---
    async def get_all_journeys(
        self, 
        db: AsyncSession, *, 
        organization_id: int, 
        requester_role: UserRole = None, # Valor padrão para evitar erro se não passado
        skip: int = 0, 
        limit: int = 100,
        driver_id: int | None = None,
        vehicle_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None
    ) -> List[Journey]:
        
        stmt = select(Journey).where(Journey.organization_id == organization_id)
        
        if date_from:
            stmt = stmt.where(Journey.start_time >= date_from)
        if date_to:
            stmt = stmt.where(Journey.start_time < date_to + timedelta(days=1))
        if driver_id:
            stmt = stmt.where(Journey.driver_id == driver_id)
        if vehicle_id:
            stmt = stmt.where(Journey.vehicle_id == vehicle_id)

        final_stmt = (
            stmt.order_by(desc(Journey.start_time))
            .options(
                selectinload(Journey.vehicle),
                selectinload(Journey.driver),
                selectinload(Journey.implement) 
            )
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(final_stmt)
        return result.scalars().all()

    # --- OUTROS MÉTODOS AUXILIARES ---
    async def get_journey(self, db: AsyncSession, *, journey_id: int, organization_id: int) -> Optional[Journey]:
        stmt = (
            select(Journey).where(Journey.id == journey_id, Journey.organization_id == organization_id)
            .options(selectinload(Journey.driver), selectinload(Journey.vehicle), selectinload(Journey.implement))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_journey(self, db: AsyncSession, *, journey_to_delete: Journey) -> Journey:
        vehicle = journey_to_delete.vehicle
        if journey_to_delete.is_active and vehicle:
            vehicle.status = VehicleStatus.AVAILABLE
            db.add(vehicle)

        await db.delete(journey_to_delete)
        await db.commit()
        return journey_to_delete

# Instância exportada
journey = CRUDJourney(Journey)