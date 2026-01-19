from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.andon_model import AndonCall, AndonStatus, AndonSector # Importe o AndonSector
from app.schemas.andon_schema import AndonCallCreate

async def create_call(db: AsyncSession, obj_in: AndonCallCreate, org_id: int, operator_id: Optional[int] = None) -> AndonCall:
    db_obj = AndonCall(
        organization_id=org_id,
        machine_id=obj_in.machine_id,
        operator_id=operator_id,
        sector=obj_in.sector,
        reason=obj_in.reason,
        description=obj_in.description,
        status=AndonStatus.OPEN
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_active_calls(
    db: AsyncSession, 
    org_id: int, 
    sector_filter: Optional[AndonSector] = None # Novo parâmetro opcional
) -> List[AndonCall]:
    
    # Base da query
    stmt = select(AndonCall).where(
        AndonCall.organization_id == org_id,
        AndonCall.status != AndonStatus.RESOLVED
    )
    
    # Se tiver filtro de setor, aplica
    if sector_filter:
        stmt = stmt.where(AndonCall.sector == sector_filter)
        
    # Ordenação
    stmt = stmt.order_by(AndonCall.opened_at.asc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

async def accept_call(db: AsyncSession, call_id: int, user_id: int) -> Optional[AndonCall]:
    stmt = select(AndonCall).where(AndonCall.id == call_id)
    result = await db.execute(stmt)
    call = result.scalars().first()
    
    if not call:
        return None
    
    call.status = AndonStatus.IN_PROGRESS
    call.accepted_at = datetime.now()
    call.accepted_by_id = user_id
    
    await db.commit()
    await db.refresh(call)
    return call

async def resolve_call(db: AsyncSession, call_id: int) -> Optional[AndonCall]:
    stmt = select(AndonCall).where(AndonCall.id == call_id)
    result = await db.execute(stmt)
    call = result.scalars().first()
    
    if not call:
        return None
    
    call.status = AndonStatus.RESOLVED
    call.resolved_at = datetime.now()
    
    await db.commit()
    await db.refresh(call)
    return call