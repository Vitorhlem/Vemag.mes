from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import deps
from app.crud import crud_andon
from app.schemas.andon_schema import AndonCallCreate, AndonCallResponse
from app.models.user_model import User
from app.models.andon_model import AndonSector # Garanta que importou o Enum

router = APIRouter()

def _format_response(call):
    return {
        "id": call.id,
        "machine_id": call.machine_id,
        "machine_name": f"Máquina {call.machine_id}", 
        "machine_sector": str(call.sector.value) if hasattr(call.sector, 'value') else str(call.sector),
        "sector": call.sector,
        "reason": call.reason,
        "description": call.description,
        "status": call.status,
        "opened_at": call.opened_at,
        "accepted_at": call.accepted_at,
        "accepted_by_name": str(call.accepted_by_id) if call.accepted_by_id else None
    }

@router.post("/", response_model=AndonCallResponse)
async def create_andon_call(
    *,
    db: AsyncSession = Depends(deps.get_db),
    andon_in: AndonCallCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    # AWAIT É OBRIGATÓRIO AQUI
    call = await crud_andon.create_call(db, andon_in, current_user.organization_id, current_user.id)
    return _format_response(call)

@router.get("/active", response_model=List[AndonCallResponse])
async def get_active_andon_calls(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Lista chamados ativos.
    - Se for GERENTE ou ADMIN: Vê tudo (Painel Geral).
    - Se for MANUTENÇÃO: Vê apenas chamados de Manutenção.
    - Se for QUALIDADE: Vê apenas chamados de Qualidade.
    - Se for OPERADOR: Vê tudo (ou pode restringir apenas à linha dele, mas geralmente vê tudo para saber status).
    """
    
    target_sector = None
    
    # Normaliza a role para maiúsculo para comparação segura
    # Assumindo que current_user.role é uma string ou Enum
    user_role = str(current_user.role).upper() if current_user.role else ""

    # --- REGRA DE NEGÓCIO: QUEM VÊ O QUE ---
    
    if user_role in ["MAINTENANCE", "MANUTENCAO", "MECANICO", "ELETRICISTA"]:
        target_sector = AndonSector.MAINTENANCE
        
    elif user_role in ["QUALITY", "QUALIDADE", "INSPETOR"]:
        target_sector = AndonSector.QUALITY
        
    elif user_role in ["LOGISTICS", "LOGISTICA", "EMPILHADEIRA"]:
        target_sector = AndonSector.LOGISTICS
        
    elif user_role in ["PCP", "PLANEJAMENTO"]:
        target_sector = AndonSector.PCP
        
    elif user_role in ["MANAGER", "GERENTE", "ADMIN", "SUPERVISOR"]:
        target_sector = None # Vê tudo (Modo TV de Gestão)
        
    else:
        # Fallback: Se for um cargo não mapeado (ex: RH), talvez não deva ver nada,
        # ou ver tudo. Vamos assumir que vê tudo por enquanto para não quebrar a TV.
        target_sector = None 

    # Chama o CRUD passando o filtro
    calls = await crud_andon.get_active_calls(
        db, 
        org_id=current_user.organization_id, 
        sector_filter=target_sector
    )
    
    return [_format_response(c) for c in calls]
@router.put("/{id}/accept", response_model=AndonCallResponse)
async def accept_andon_call(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    # AWAIT É OBRIGATÓRIO AQUI
    call = await crud_andon.accept_call(db, id, current_user.id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return _format_response(call)

@router.put("/{id}/resolve", response_model=AndonCallResponse)
async def resolve_andon_call(
    *,
    db: AsyncSession = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    # AWAIT É OBRIGATÓRIO AQUI
    call = await crud_andon.resolve_call(db, id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return _format_response(call)