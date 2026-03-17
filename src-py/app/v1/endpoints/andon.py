from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app import deps
from sqlalchemy import select
from app.crud import crud_andon
from app.models.machine_model import Machine
from app.db.session import async_session
from app.schemas.andon_schema import AndonCallCreate, AndonCallResponse
from app.models.user_model import User, UserRole
from app.services.fcm_service import enviar_push_lista
from app.models.andon_model import AndonSector, AndonStatus
from app.tasks.andon_tasks import processar_novo_chamado
from app.core.websocket_manager import manager
from fastapi import WebSocket, WebSocketDisconnect

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

async def notificar_setor_andon(setor_str: str, maquina: str, motivo: str, obs: str, org_id: int):
    async with async_session() as db:
        try:
            setor = setor_str.upper().strip()
            chefia = [UserRole.MANAGER, UserRole.ADMIN, UserRole.CLIENTE_ATIVO, UserRole.CLIENTE_DEMO]

            role_map = {
                "MANUTENÇÃO": [UserRole.MAINTENANCE] + chefia,
                "MANUTENCAO": [UserRole.MAINTENANCE] + chefia,
                "ELÉTRICA":   [UserRole.MAINTENANCE] + chefia,
                "LOGÍSTICA":  [UserRole.LOGISTICS] + chefia,
                "LOGISTICA":  [UserRole.LOGISTICS] + chefia,
                "PCP":        [UserRole.PCP] + chefia,
                "QUALIDADE":  [UserRole.QUALITY] + chefia,
                "SEGURANÇA":  chefia,
                "PROCESSO":   chefia
            }
            
            roles_alvo = role_map.get(setor, chefia)
            
            query = select(User.device_token).where(
                User.organization_id == org_id,
                User.role.in_(roles_alvo),
                User.device_token.isnot(None)
            )
            
            result = await db.execute(query)
            tokens = result.scalars().all()
            
            if tokens:
                corpo = f"Máquina: {maquina}\nMotivo: {motivo}"
                if obs:
                    corpo += f"\nObs: {obs}"

                enviar_push_lista(
                    tokens=list(tokens),
                    title=f"🚨 Ajuda: {setor_str}", 
                    body=corpo,
                    data={"tipo": "andon", "setor": setor_str}
                )
                print(f"📢 Andon Push enviado para {len(tokens)} dispositivos.")
        except Exception as e:
            print(f"❌ Erro no Push Andon: {e}")

@router.websocket("/ws/{org_id}")
async def andon_websocket(websocket: WebSocket, org_id: int):
    # Agora esta linha funcionará porque atualizamos o ConnectionManager
    await manager.connect(websocket, org_id=org_id) 
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, org_id=org_id)

@router.post("/", response_model=AndonCallResponse)
async def create_andon_call(
    *,
    db: AsyncSession = Depends(deps.get_db),
    andon_in: AndonCallCreate,
    current_user: User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks
) -> Any:
    setor_original = andon_in.sector
    
    db_sector_map = {
        "ELÉTRICA": AndonSector.MAINTENANCE, "ELETRICA": AndonSector.MAINTENANCE,
        "MANUTENÇÃO": AndonSector.MAINTENANCE, "MANUTENCAO": AndonSector.MAINTENANCE,
        "LOGÍSTICA": AndonSector.LOGISTICS, "LOGISTICA": AndonSector.LOGISTICS,
        "PCP": AndonSector.PCP,
        "QUALIDADE": AndonSector.QUALITY,
        "SEGURANÇA": AndonSector.SECURITY, "SEGURANCA": AndonSector.SECURITY,
        "GERENTE": AndonSector.MANAGER,
        "PROCESSO": AndonSector.MANAGER
    }

    enum_sector = db_sector_map.get(setor_original.upper(), AndonSector.MANAGER)
    andon_in.sector = enum_sector

    call = await crud_andon.create_call(db, andon_in, current_user.organization_id, current_user.id)
    
    res = _format_response(call)
    res["sector"] = setor_original 

    processar_novo_chamado.delay(
        call_id=call.id,
        machine_name=res["machine_name"],
        sector=setor_original,
        organization_id=current_user.organization_id,
        call_data=res
    )

    background_tasks.add_task(
        notificar_setor_andon,
        setor_str=setor_original,
        maquina=res["machine_name"],
        motivo=andon_in.reason or "Solicitação via Tablet",
        obs=andon_in.description or "",
        org_id=current_user.organization_id
    )

    # CORREÇÃO AQUI: Passar org_id no broadcast
    await manager.broadcast({"type": "NEW_CALL", "data": res}, org_id=current_user.organization_id)

    return res

@router.get("/active", response_model=List[AndonCallResponse])
async def get_active_andon_calls(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    
    # 1. Mapeia quem pode ver o quê
    allowed_sectors = None # None significa "Vê tudo" (Gerentes/Admins)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        if current_user.role == UserRole.MAINTENANCE:
            allowed_sectors = [AndonSector.MAINTENANCE]
        elif current_user.role == UserRole.LOGISTICS:
            allowed_sectors = [AndonSector.LOGISTICS]
        elif current_user.role == UserRole.PCP:
            allowed_sectors = [AndonSector.PCP]
        elif current_user.role == UserRole.QUALITY:
            allowed_sectors = [AndonSector.QUALITY]
        else:
            allowed_sectors = [] # Se for um cargo sem setor mapeado, não vê nada
            
    # 2. Pede pro banco apenas os chamados permitidos
    calls = await crud_andon.get_active_calls(
        db, 
        org_id=current_user.organization_id, 
        sector_filters=allowed_sectors
    )
    
    return [_format_response(c) for c in calls]

@router.put("/{id}/accept", response_model=AndonCallResponse)
async def accept_andon_call(
    *, db: AsyncSession = Depends(deps.get_db), id: int, current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    call = await crud_andon.accept_call(db, id, current_user.id)
    if not call: raise HTTPException(404, "Call not found")
    
    # CORREÇÃO AQUI: Passar org_id no broadcast
    await manager.broadcast(
        {"type": "UPDATE_CALL", "data": _format_response(call)}, 
        org_id=current_user.organization_id
    )
    return _format_response(call)

@router.put("/{id}/resolve", response_model=AndonCallResponse)
async def resolve_andon_call(
    *, db: AsyncSession = Depends(deps.get_db), id: int, current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    call = await crud_andon.resolve_call(db, id)
    if not call: raise HTTPException(404, "Call not found")
    
    # CORREÇÃO AQUI: Passar org_id no broadcast
    await manager.broadcast(
        {"type": "UPDATE_CALL", "data": _format_response(call)}, 
        org_id=current_user.organization_id
    )
    return _format_response(call)