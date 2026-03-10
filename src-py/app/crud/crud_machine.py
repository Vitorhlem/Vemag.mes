from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from sqlalchemy import update as sql_update
from typing import List, Optional
from fastapi.encoders import jsonable_encoder

from app.models.machine_model import Machine
from app.models.part_model import InventoryItem
from app.schemas.machine_schema import MachineCreate, MachineUpdate

# --- FUNÇÕES DIRETAS (SEM CLASSE) ---

async def get(db: AsyncSession, *, machine_id: int, organization_id: int) -> Optional[Machine]:
    """Busca um veículo pelo ID, garantindo que pertence à organização."""
    stmt = select(Machine).where(Machine.id == machine_id, Machine.organization_id == organization_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_multi_by_org(
    db: AsyncSession,
    *,
    organization_id: int,
    skip: int = 0,
    limit: int = 8,
    search: Optional[str] = None
) -> List[Machine]:
    stmt = select(Machine).where(Machine.organization_id == organization_id)

    if search and search.strip():
        search_term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Machine.brand).like(search_term),
                func.lower(Machine.model).like(search_term),
                func.lower(Machine.identifier).like(search_term),
                func.lower(Machine.identifier).like(search_term)
            )
        )

    stmt = stmt.order_by(Machine.brand).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def count_by_org(db: AsyncSession, *, organization_id: int, search: Optional[str] = None) -> int:
    """Conta o número total de veículos para paginação."""
    stmt = select(func.count()).select_from(Machine).where(Machine.organization_id == organization_id)

    if search and search.strip():
        search_term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Machine.brand).like(search_term),
                func.lower(Machine.model).like(search_term),
                func.lower(Machine.identifier).like(search_term),
                func.lower(Machine.identifier).like(search_term)
            )
        )
    
    result = await db.execute(stmt)
    return result.scalar_one()

async def count(db: AsyncSession, *, organization_id: int) -> int:
    return await count_by_org(db, organization_id=organization_id, search=None)

# --- CORREÇÃO: REMOVIDO O 'self' DESTA FUNÇÃO ---
async def create_with_owner(
    db: AsyncSession, *, obj_in: MachineCreate, organization_id: int
) -> Machine:
    obj_in_data = jsonable_encoder(obj_in)
    
    db_obj = Machine(
        **obj_in_data, 
        organization_id=organization_id
    )
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
    
async def update(db: AsyncSession, *, db_machine: Machine, machine_in: MachineUpdate) -> Machine:
    update_data = machine_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_machine, field, value)
    db.add(db_machine)
    await db.commit()
    await db.refresh(db_machine)
    return db_machine

async def remove(db: AsyncSession, *, db_machine: Machine) -> Machine:
    stmt = sql_update(InventoryItem).where(InventoryItem.installed_on_machine_id == db_machine.id).values(installed_on_machine_id=None)
    await db.execute(stmt)
    
    await db.delete(db_machine)
    await db.commit()
    return db_machine

async def get_by_id(db: AsyncSession, *, id: int) -> Optional[Machine]:
    stmt = select(Machine).where(Machine.id == id)
    result = await db.execute(stmt)
    return result.scalars().first()