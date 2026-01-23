from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import deps
from app.crud import crud_andon
from app.schemas.andon_schema import AndonCallCreate, AndonCallResponse
from app.models.user_model import User
from app.models.andon_model import AndonSector, AndonStatus

router = APIRouter()

def _format_response(call):
    # Formatação Segura
    m_name = f"Máquina {call.machine_id}"
    if call.machine:
        m_name = f"{call.machine.brand} {call.machine.model}"
        
    op_name = "---"
    if call.operator:
        op_name = call.operator.full_name or call.operator.email
        
    tech_name = None
    if call.accepted_by:
        tech_name = call.accepted_by.full_name
    elif call.accepted_by_id:
        tech_name = f"ID {call.accepted_by_id}"

    # Setor (Enum para String)
    sector_str = str(call.sector.value) if hasattr(call.sector, 'value') else str(call.sector)

    return {
        "id": call.id,
        "machine_id": call.machine_id,
        "machine_name": m_name, 
        "machine_sector": "Produção",
        "sector": sector_str,
        "reason": call.reason,
        "description": call.description,
        "status": call.status,
        "opened_at": call.opened_at,
        "accepted_at": call.accepted_at,
        "accepted_by_name": tech_name,
        "operator_name": op_name
    }

@router.post("/", response_model=AndonCallResponse)
async def create_andon_call(
    *,
    db: AsyncSession = Depends(deps.get_db),
    andon_in: AndonCallCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    # LOG DE DEBUG
    print(f"➕ [ANDON] Criando chamado. Máquina: {andon_in.machine_id}, Setor: {andon_in.sector}, Org: {current_user.organization_id}")

    # Mapper de Setor (Front UPPER -> Enum Title)
    sector_map = {
        "MANUTENÇÃO": AndonSector.MAINTENANCE, "MANUTENCAO": AndonSector.MAINTENANCE,
        "QUALIDADE": AndonSector.QUALITY, "LOGISTICA": AndonSector.LOGISTICS,
        "PCP": AndonSector.PCP, "GERENTE": AndonSector.MANAGER,
        "SEGURANÇA": AndonSector.SECURITY
    }
    
    # Corrige setor se necessário
    if andon_in.sector.upper() in sector_map:
        andon_in.sector = sector_map[andon_in.sector.upper()]

    call = await crud_andon.create_call(db, andon_in, current_user.organization_id, current_user.id)
    return _format_response(call)

@router.get("/active", response_model=List[AndonCallResponse])
async def get_active_andon_calls(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    # LOG DE DEBUG
    print(f"🔍 [ANDON BOARD] Usuário: {current_user.email} (Org: {current_user.organization_id}) buscando ativos...")
    
    # Sem filtro de setor (mostra tudo para testar)
    target_sector = None 

    calls = await crud_andon.get_active_calls(
        db, 
        org_id=current_user.organization_id, 
        sector_filter=target_sector
    )
    
    print(f"✅ [ANDON BOARD] Encontrados: {len(calls)} chamados ativos.")
    
    return [_format_response(c) for c in calls]

@router.put("/{id}/accept", response_model=AndonCallResponse)
async def accept_andon_call(
    *, db: AsyncSession = Depends(deps.get_db), id: int, current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    call = await crud_andon.accept_call(db, id, current_user.id)
    if not call: raise HTTPException(404, "Call not found")
    return _format_response(call)

@router.put("/{id}/resolve", response_model=AndonCallResponse)
async def resolve_andon_call(
    *, db: AsyncSession = Depends(deps.get_db), id: int, current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    call = await crud_andon.resolve_call(db, id)
    if not call: raise HTTPException(404, "Call not found")
    return _format_response(call)