from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from sqlalchemy import update as sql_update
from typing import List, Optional
from fastapi.encoders import jsonable_encoder

from app.models.vehicle_model import Vehicle
from app.models.part_model import InventoryItem
from app.schemas.telemetry_schema import TelemetryPayload
from app.schemas.vehicle_schema import VehicleCreate, VehicleUpdate

# --- FUNÇÕES DIRETAS (SEM CLASSE) ---

async def get(db: AsyncSession, *, vehicle_id: int, organization_id: int) -> Optional[Vehicle]:
    """Busca um veículo pelo ID, garantindo que pertence à organização."""
    stmt = select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.organization_id == organization_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_multi_by_org(
    db: AsyncSession,
    *,
    organization_id: int,
    skip: int = 0,
    limit: int = 8,
    search: Optional[str] = None
) -> List[Vehicle]:
    stmt = select(Vehicle).where(Vehicle.organization_id == organization_id)

    if search and search.strip():
        search_term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Vehicle.brand).like(search_term),
                func.lower(Vehicle.model).like(search_term),
                func.lower(Vehicle.license_plate).like(search_term),
                func.lower(Vehicle.identifier).like(search_term)
            )
        )

    stmt = stmt.order_by(Vehicle.brand).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def count_by_org(db: AsyncSession, *, organization_id: int, search: Optional[str] = None) -> int:
    """Conta o número total de veículos para paginação."""
    stmt = select(func.count()).select_from(Vehicle).where(Vehicle.organization_id == organization_id)

    if search and search.strip():
        search_term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Vehicle.brand).like(search_term),
                func.lower(Vehicle.model).like(search_term),
                func.lower(Vehicle.license_plate).like(search_term),
                func.lower(Vehicle.identifier).like(search_term)
            )
        )
    
    result = await db.execute(stmt)
    return result.scalar_one()

async def count(db: AsyncSession, *, organization_id: int) -> int:
    return await count_by_org(db, organization_id=organization_id, search=None)

async def update_vehicle_from_telemetry(db: AsyncSession, *, payload: TelemetryPayload) -> Optional[Vehicle]:
    stmt = select(Vehicle).where(Vehicle.telemetry_device_id == payload.device_id)
    result = await db.execute(stmt)
    vehicle_obj = result.scalar_one_or_none()

    if not vehicle_obj:
        print(f"AVISO: Recebida telemetria de um dispositivo não registrado: {payload.device_id}")
        return None

    vehicle_obj.last_latitude = payload.latitude
    vehicle_obj.last_longitude = payload.longitude
    if payload.engine_hours > (vehicle_obj.current_engine_hours or 0):
        vehicle_obj.current_engine_hours = payload.engine_hours
    
    db.add(vehicle_obj)
    await db.commit()
    await db.refresh(vehicle_obj)
    return vehicle_obj

# --- CORREÇÃO: REMOVIDO O 'self' DESTA FUNÇÃO ---
async def create_with_owner(
    db: AsyncSession, *, obj_in: VehicleCreate, organization_id: int
) -> Vehicle:
    obj_in_data = jsonable_encoder(obj_in)
    
    db_obj = Vehicle(
        **obj_in_data, 
        organization_id=organization_id
    )
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
    
async def update(db: AsyncSession, *, db_vehicle: Vehicle, vehicle_in: VehicleUpdate) -> Vehicle:
    update_data = vehicle_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)
    db.add(db_vehicle)
    await db.commit()
    await db.refresh(db_vehicle)
    return db_vehicle

async def remove(db: AsyncSession, *, db_vehicle: Vehicle) -> Vehicle:
    stmt = sql_update(InventoryItem).where(InventoryItem.installed_on_vehicle_id == db_vehicle.id).values(installed_on_vehicle_id=None)
    await db.execute(stmt)
    
    await db.delete(db_vehicle)
    await db.commit()
    return db_vehicle

async def get_by_id(db: AsyncSession, *, id: int) -> Optional[Vehicle]:
    stmt = select(Vehicle).where(Vehicle.id == id)
    result = await db.execute(stmt)
    return result.scalars().first()