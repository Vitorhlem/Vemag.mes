from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.andon_model import AndonCall, AndonStatus, AndonSector
from app.schemas.andon_schema import AndonCallCreate

async def create_call(db: AsyncSession, obj_in: AndonCallCreate, org_id: int, operator_id: Optional[int] = None) -> AndonCall:
    # 1. Cria e Salva
    db_obj = AndonCall(
        organization_id=org_id,
        machine_id=obj_in.machine_id,
        operator_id=operator_id,
        sector=obj_in.sector,
        reason=obj_in.reason,
        description=obj_in.description,
        status=AndonStatus.OPEN,
        opened_at=datetime.now()
    )
    db.add(db_obj)
    await db.commit()
    
    # 2. Recarrega IMEDIATAMENTE com todos os dados (Evita erro MissingGreenlet)
    stmt = select(AndonCall).options(
        selectinload(AndonCall.machine),
        selectinload(AndonCall.operator),
        selectinload(AndonCall.accepted_by)
    ).where(AndonCall.id == db_obj.id)
    
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_active_calls(
    db: AsyncSession, 
    org_id: int, 
    sector_filter: Optional[AndonSector] = None 
) -> List[AndonCall]:
    
    # Carrega Máquina, Operador e Técnico junto com o chamado
    stmt = select(AndonCall).options(
        selectinload(AndonCall.machine),
        selectinload(AndonCall.operator),
        selectinload(AndonCall.accepted_by)
    ).where(
        AndonCall.organization_id == org_id,
        AndonCall.status != AndonStatus.RESOLVED
    )
    
    if sector_filter:
        stmt = stmt.where(AndonCall.sector == sector_filter)
        
    stmt = stmt.order_by(AndonCall.opened_at.asc())
    
    result = await db.execute(stmt)
    return result.scalars().all()

async def accept_call(db: AsyncSession, call_id: int, user_id: int) -> Optional[AndonCall]:
    # Busca primeiro
    stmt = select(AndonCall).where(AndonCall.id == call_id)
    result = await db.execute(stmt)
    call = result.scalars().first()
    
    if not call: return None
    
    # Atualiza
    call.status = AndonStatus.IN_PROGRESS
    call.accepted_at = datetime.now()
    call.accepted_by_id = user_id
    
    await db.commit()
    
    # Recarrega completo para retorno
    stmt_refresh = select(AndonCall).options(
        selectinload(AndonCall.machine),
        selectinload(AndonCall.operator),
        selectinload(AndonCall.accepted_by)
    ).where(AndonCall.id == call_id)
    
    return (await db.execute(stmt_refresh)).scalars().first()

async def resolve_call(db: AsyncSession, call_id: int) -> Optional[AndonCall]:
    # 1. Busca o chamado
    stmt = select(AndonCall).where(AndonCall.id == call_id)
    result = await db.execute(stmt)
    call = result.scalars().first()
    
    if not call:
        return None
    
    # 2. Atualiza os dados
    call.status = AndonStatus.RESOLVED
    call.resolved_at = datetime.now()
    
    await db.commit()
    
    # 3. [CORREÇÃO] Recarrega o objeto COMPLETO com os relacionamentos
    # (Isso evita o erro MissingGreenlet na hora de devolver a resposta JSON)
    stmt_refresh = select(AndonCall).options(
        selectinload(AndonCall.machine),
        selectinload(AndonCall.operator),
        selectinload(AndonCall.accepted_by)
    ).where(AndonCall.id == call_id)
    
    result_refresh = await db.execute(stmt_refresh)
    return result_refresh.scalars().first()