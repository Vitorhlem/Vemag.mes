from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple, Union, Dict, Any
from sqlalchemy import func, desc 

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
        if journey_in.implement_id:
            implement = await db.get(Implement, journey_in.implement_id)
            if not implement or implement.organization_id != organization_id:
                raise ValueError("Implemento não encontrado.")
            if implement.status != ImplementStatus.AVAILABLE:
                raise VehicleNotAvailableError(f"O implemento {implement.name} não está disponível.")
            implement.status = ImplementStatus.IN_USE
            db.add(implement)
        
        if not journey_in.vehicle_id:
            raise ValueError("O ID do veículo é obrigatório.")
            
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
                
                # --- ATUALIZAÇÃO DO HORÍMETRO/KM ---
                if journey_in.end_engine_hours is not None:
                    current = vehicle.current_engine_hours or 0
                    if journey_in.end_engine_hours >= current:
                        vehicle.current_engine_hours = journey_in.end_engine_hours
                
                elif journey_in.end_mileage is not None:
                    current_km = vehicle.current_km or 0
                    if journey_in.end_mileage >= current_km:
                        vehicle.current_km = journey_in.end_mileage
                # -----------------------------------

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

                db.add(vehicle) # Persiste a atualização do veículo
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

    async def get_multi_by_org(
        self, db: AsyncSession, *, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[Journey]:
        stmt = (
            select(Journey)
            .where(Journey.organization_id == organization_id)
            .options(
                selectinload(Journey.vehicle),
                selectinload(Journey.driver),
                selectinload(Journey.implement) 
            )
            .order_by(desc(Journey.start_time))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

journey = CRUDJourney(Journey)