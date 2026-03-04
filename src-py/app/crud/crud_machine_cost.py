from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload 
from typing import List, Optional
from datetime import date
from sqlalchemy import func  # <--- IMPORTANTE: Adicionado func

from app.models.machine_cost_model import MachineCost
from app.schemas.machine_cost_schema import MachineCostCreate


async def create_cost(
    db: AsyncSession, *, obj_in: MachineCostCreate, machine_id: int, organization_id: int, commit: bool = True
) -> MachineCost:
    """Regista um novo custo para um veículo."""
    db_obj = MachineCost(
        **obj_in.model_dump(),
        machine_id=machine_id,
        organization_id=organization_id
    )
    db.add(db_obj)
    
    if commit:
        await db.commit()
        await db.refresh(db_obj, attribute_names=["machine"])
        
    return db_obj


async def get_costs_by_machine(
    db: AsyncSession, *, machine_id: int, skip: int = 0, limit: int = 100
) -> List[MachineCost]:
    """Busca a lista de custos para um veículo específico."""
    stmt = (
        select(MachineCost)
        .where(MachineCost.machine_id == machine_id)
        .options(selectinload(MachineCost.machine))
        .order_by(MachineCost.date.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_costs_by_organization(
    db: AsyncSession, 
    *, 
    organization_id: int, 
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[MachineCost]:
    """Busca a lista de custos para uma organização inteira, com filtros de data."""
    stmt = (
        select(MachineCost)
        .where(MachineCost.organization_id == organization_id)
        .options(selectinload(MachineCost.machine))
        .order_by(MachineCost.date.desc())
    )
    
    if start_date:
        stmt = stmt.where(MachineCost.date >= start_date)
    if end_date:
        stmt = stmt.where(MachineCost.date <= end_date)
        
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    return result.scalars().all()

# --- NOVA FUNÇÃO DE CONTAGEM REAL ---
async def count_costs_in_current_month(db: AsyncSession, *, organization_id: int) -> int:
    """Conta quantos registros de custo uma organização criou no mês corrente."""
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Lógica para encontrar o primeiro dia do próximo mês
    if start_of_month.month == 12:
        start_of_next_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
    else:
        start_of_next_month = start_of_month.replace(month=start_of_month.month + 1)

    stmt = (
        select(func.count(MachineCost.id))
        .where(
            MachineCost.organization_id == organization_id,
            MachineCost.date >= start_of_month,
            MachineCost.date < start_of_next_month
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()