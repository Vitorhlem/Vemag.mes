from fastapi import APIRouter, Depends, HTTPException, Response, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from datetime import datetime
import uuid
import shutil
from sqlalchemy.orm import selectinload
import json
from app.services.production_service import ProductionService
from app.schemas.production_schema import ProductionEventCreate
from app import crud, deps
from app.core.config import settings 
from app.core.email_utils import send_email 
from app.models.user_model import User, UserRole
from app.core.websocket_manager import manager
# Schemas
from app.schemas.maintenance_schema import (
    MaintenanceRequestPublic, MaintenanceRequestCreate, MaintenanceRequestUpdate,
    MaintenanceCommentPublic, MaintenanceCommentCreate,
    ReplaceComponentPayload, ReplaceComponentResponse, InstallComponentResponse,
    InstallComponentPayload,
    MaintenanceServiceItemCreate, MaintenanceServiceItemPublic, MaintenanceRequestPublic
)
from app.schemas.audit_log_schema import AuditLogCreate

# Models e CRUDs
from app.crud import crud_audit_log
from app.crud.crud_demo_usage import demo_usage as demo_usage_crud
from app.models.maintenance_model import MaintenanceComment, MaintenancePartChange, MaintenanceServiceItem, MaintenanceRequest, MaintenanceCategory, MaintenanceServiceItem
from app.models.vehicle_cost_model import VehicleCost, CostType 
from app.models.notification_model import NotificationType
from app.models.inventory_transaction_model import InventoryTransaction
from app.models.vehicle_component_model import VehicleComponent
# Import do Vehicle para mudar status
try:
    from app.models.vehicle_model import Vehicle, VehicleStatus
except ImportError:
    from app.models.vehicle_model import Vehicle, VehicleStatus

router = APIRouter()

# --- EMAIL HELPER ---
def send_email_background_task(manager_emails: List[str], request_id: int, reporter_name: str, vehicle_info: str, description: str, category: str):
    if not manager_emails: return
    subject = f"Novo Chamado de Manutenção Aberto - TruCar #{request_id}"
    frontend_link = "https://trucar.netlify.app/#/maintenance" 
    message_html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <body>
        <div style="font-family: sans-serif; max-width: 600px; margin: auto;">
            <h2 style="color: #2D3748;">TruCar - Novo Chamado #{request_id}</h2>
            <p>Solicitante: {reporter_name}</p>
            <p>Veículo: {vehicle_info}</p>
            <p>Categoria: {category}</p>
            <p><b>Problema:</b> {description}</p>
            <a href="{frontend_link}" style="background: #3B82F6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Ver Sistema</a>
        </div>
    </body>
    </html>
    """
    try:
        send_email(to_emails=manager_emails, subject=subject, message_html=message_html)
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

# ============================================================================
# ROTAS (HÍBRIDAS: Aceitam /requests e /raiz)
# ============================================================================

def parse_dt(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str or dt_str.strip() == "": return None
    try: return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except: return None

def safe_float(v, default=0.0):
    try: return float(v) if v else default
    except: return default

@router.post("/industrial-os", response_model=MaintenanceRequestPublic)
async def create_industrial_os(payload: dict, db: AsyncSession = Depends(deps.get_db), current_user = Depends(deps.get_current_active_user)):
    try:
        os_id = payload.get("id")
        v_id = int(payload.get("vehicle_id"))

        l_total = safe_float(payload.get("labor_total"))
        m_total = safe_float(payload.get("material_total"))
        s_total = safe_float(payload.get("services_total"))
        o_total = safe_float(payload.get("others_total"))
        grand_total = l_total + m_total + s_total + o_total

        metadata = json.dumps({
            "elaborated_by": payload.get("elaborated_by", ""),
            "supervisor": payload.get("supervisor", ""),
            "responsible": payload.get("responsible", ""), # Salva o responsável aqui
            "labor_total": safe_float(payload.get("labor_total")),
            "material_total": safe_float(payload.get("material_total")),
            "services_total": safe_float(payload.get("services_total")),
            "others_total": safe_float(payload.get("others_total")),
            # IMPORTANTE: Salva os arrays para o Frontend ler depois
            "labor_rows": payload.get("labor_rows", []),
            "material_rows": payload.get("material_rows", []),
            "third_party_rows": payload.get("third_party_rows", [])
        }, ensure_ascii=False)

        common = {
            "vehicle_id": v_id, 
            "cost_center": payload.get("cost_center"),
            "responsible": payload.get("responsible"), # Salva na coluna oficial
            "supervisor": payload.get("supervisor"),
            "stopped_at": parse_dt(payload.get("stopped_at")),
            "returned_at": parse_dt(payload.get("returned_at")),
            "maintenance_type": payload.get("maintenance_type"),
            "problem_description": payload.get("executed_services"),
            "status": payload.get("status"), 
            "manager_notes": metadata, # O JSON completo com as tabelas
            "total_cost": grand_total, # <--- SALVA O VALOR NUMÉRICO TOTAL AQUI
            "category": payload.get("category", MaintenanceCategory.OTHER)
        }

        if os_id:
            db_os = await db.get(MaintenanceRequest, os_id)
            for k, v in common.items(): setattr(db_os, k, v)
            await db.execute(delete(MaintenanceServiceItem).where(MaintenanceServiceItem.maintenance_request_id == os_id))
            new_os = db_os
        else:
            new_os = MaintenanceRequest(**common, organization_id=current_user.organization_id, reported_by_id=current_user.id)
            db.add(new_os)

        await db.flush()
        for key, itype in [("labor_rows", "LABOR"), ("material_rows", "MATERIAL"), ("third_party_rows", "THIRD_PARTY")]:
            for row in payload.get(key, []):
                if row.get("description"):
                    # CORREÇÃO: Tenta pegar 'price' ou 'cost' para garantir compatibilidade
                    item_cost = safe_float(row.get("price") if row.get("price") is not None else row.get("cost"))
                    
                    db.add(MaintenanceServiceItem(
                        description=row["description"], 
                        quantity=safe_float(row.get("qty") if row.get("qty") is not None else row.get("quantity"), 1.0),
                        cost=item_cost, # <--- Agora o valor será salvo corretamente
                        item_type="THIRD_PARTY", # <--- ADICIONE ESTA LINHA PARA CORRIGIR O ERRO
                        maintenance_request_id=new_os.id, 
                        added_by_id=current_user.id,
                        
                    ))

        if new_os.status == "CONCLUIDA":
            v = await db.get(Vehicle, v_id)
            if v: 
                v.status = VehicleStatus.AVAILABLE.value
                
                # ✅ NOVIDADE: Gera o evento de Fim de Manutenção no Histórico
                event = ProductionEventCreate(
                    machine_id=v.id,
                    event_type="STATUS_CHANGE",
                    new_status="AVAILABLE",
                    reason="Fim de Manutenção (O.S. Industrial)",
                    operator_badge="SISTEMA"
                )
                await ProductionService.handle_event(db, event)

        await db.commit()
        stmt = select(MaintenanceRequest).where(MaintenanceRequest.id == new_os.id).options(
            selectinload(MaintenanceRequest.vehicle),
            selectinload(MaintenanceRequest.services),
            selectinload(MaintenanceRequest.comments).selectinload(MaintenanceComment.user),
            selectinload(MaintenanceRequest.part_changes).selectinload(MaintenancePartChange.user),
            selectinload(MaintenanceRequest.part_changes).selectinload(MaintenancePartChange.component_removed),
            selectinload(MaintenanceRequest.part_changes).selectinload(MaintenancePartChange.component_installed),
            selectinload(MaintenanceRequest.reporter),
            selectinload(MaintenanceRequest.approver)
        )
        res = await db.execute(stmt)
        return res.scalars().first()
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc() # type: ignore
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/industrial-os/{os_id}")
async def delete_industrial_os(os_id: int, db: AsyncSession = Depends(deps.get_db)):
    os_req = await db.get(MaintenanceRequest, os_id)
    if os_req:
        await db.delete(os_req)
        await db.commit()
    return {"ok": True}

# 1. CRIAR CHAMADO
@router.post("/requests", response_model=MaintenanceRequestPublic, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=MaintenanceRequestPublic, status_code=status.HTTP_201_CREATED)
async def create_maintenance_request(
    *,
    db: AsyncSession = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    request_in: MaintenanceRequestCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    # Validação Demo
    is_demo_org = False
    if current_user.role == UserRole.CLIENTE_DEMO: is_demo_org = True
    elif current_user.role == UserRole.DRIVER:
        stmt = select(User).where(User.organization_id == current_user.organization_id, User.role == UserRole.CLIENTE_DEMO).limit(1)
        if (await db.execute(stmt)).scalars().first(): is_demo_org = True

    if is_demo_org:
        limit = settings.DEMO_MONTHLY_LIMITS.get("maintenance_requests", 5)
        current = await crud.maintenance.count_requests_in_current_month(db, organization_id=current_user.organization_id)
        if current >= limit:
            raise HTTPException(status_code=403, detail=f"Limite mensal de {limit} chamados atingido.")

    try:
        # Cria a O.M.
        request = await crud.maintenance.create_request(
            db=db, request_in=request_in, reporter_id=current_user.id, organization_id=current_user.organization_id
        )
        
        # --- BLOQUEIA A MÁQUINA (STATUS: EM MANUTENÇÃO) ---
        vehicle = await db.get(Vehicle, request_in.vehicle_id)
        if vehicle:
            print(f"[DEBUG] O.M. Aberta. Bloqueando veículo {vehicle.id} para {VehicleStatus.MAINTENANCE.value}.")
            vehicle.status = VehicleStatus.MAINTENANCE.value
            db.add(vehicle)
        # --------------------------------------------------

        if is_demo_org:
            await crud.demo_usage.increment_usage(db, organization_id=current_user.organization_id, resource_type="maintenances")
        
        response = MaintenanceRequestPublic.model_validate(request)

        # Notificações
        msg = f"Nova solicitação para {request.vehicle.brand} {request.vehicle.model} por {current_user.full_name}."
        background_tasks.add_task(
            crud.notification.create_notification,
            db=db, message=msg, notification_type=NotificationType.MAINTENANCE_REQUEST_NEW,
            organization_id=current_user.organization_id, send_to_managers=True,
            related_entity_type="maintenance_request", related_entity_id=request.id,
            related_vehicle_id=request.vehicle_id
        )

        managers = await crud.user.get_managers_emails(db, organization_id=current_user.organization_id)
        if current_user.email and current_user.email not in managers: managers.append(current_user.email)
        
        if managers:
            v_info = f"{request.vehicle.brand} {request.vehicle.model} ({request.vehicle.license_plate or 'S/ Placa'})"
            background_tasks.add_task(send_email_background_task, managers, request.id, current_user.full_name, v_info, request.problem_description, request.category.value)

        # Audit
        await crud_audit_log.create(db=db, log_in=AuditLogCreate(
            action="CREATE", resource_type="Chamado de Manutenção", resource_id=str(request.id),
            user_id=current_user.id, organization_id=current_user.organization_id,
            details={"vehicle_id": request.vehicle_id, "problem": request.problem_description}
        ))
        
        await db.commit()
        return response
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# 2. LISTAR
@router.get("/", response_model=List[MaintenanceRequestPublic])
@router.get("/requests", response_model=List[MaintenanceRequestPublic])
async def read_maintenance_requests(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    vehicleId: int | None = None,
):
    requests = await crud.maintenance.get_all_requests(
        db=db, organization_id=current_user.organization_id, 
        search=search, skip=skip, limit=limit, vehicle_id=vehicleId
    )
    if current_user.role == UserRole.DRIVER:
        return [req for req in requests if req.reported_by_id == current_user.id]
    return requests

# 3. DELETAR
@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_maintenance_request(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request_id: int,
    current_user: User = Depends(deps.get_current_active_manager),
):
    req = await crud.maintenance.get_request(db=db, request_id=request_id, organization_id=current_user.organization_id)
    if not req: raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    await crud.maintenance.delete_request(db=db, request_to_delete=req)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# 4. ATUALIZAR STATUS (CORREÇÃO DA LIBERAÇÃO)
@router.put("/requests/{request_id}/status", response_model=MaintenanceRequestPublic)
@router.put("/{request_id}/status", response_model=MaintenanceRequestPublic)
async def update_request_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    request_id: int,
    request_in: MaintenanceRequestUpdate,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """
    Atualiza o status da O.M. e, se for concluída, libera a máquina automaticamente no MES.
    """
    db_obj = await crud.maintenance.get_request(db, request_id=request_id, organization_id=current_user.organization_id)
    if not db_obj: 
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    
    # 1. Atualiza os dados da O.M.
    update_data = request_in.model_dump(exclude_unset=True)
    for field in update_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    
    # 2. Verifica se o novo status representa "Finalizado"
    # Normaliza para maiúsculo para evitar erro de digitação (ex: "Concluida", "CONCLUIDA")
    new_status_val = str(db_obj.status.value if hasattr(db_obj.status, 'value') else db_obj.status).upper()
    finished_keywords = ["COMPLETED", "CONCLUIDO", "CONCLUIDA", "CONCLUÍDA", "CLOSED", "FECHADO", "CANCELED", "CANCELADO", "REJECTED"]
    
    if any(k in new_status_val for k in finished_keywords):
        vehicle = await db.get(Vehicle, db_obj.vehicle_id)
        
        # Só libera se o veículo existir e NÃO estiver já disponível (evita log duplicado)
        if vehicle and "DISPON" not in str(vehicle.status).upper() and "AVAILABLE" not in str(vehicle.status).upper():
            print(f"🔓 [AUTO] O.M. #{request_id} finalizada. Liberando Máquina {vehicle.id}...")

            # A. Gera o evento de histórico no MES (Fecha o card de manutenção)
            event = ProductionEventCreate(
                machine_id=vehicle.id,
                event_type="STATUS_CHANGE",
                new_status="AVAILABLE",
                reason=f"Fim de Manutenção (O.M. #{request_id})", # <--- ADICIONEI O ID DA O.M. AQUI
                operator_badge="SISTEMA"
            )
            # O handle_event já cuida de fechar a fatia de tempo anterior e abrir a nova (IDLE)
            await ProductionService.handle_event(db, event)
            
            # B. Atualiza o status oficial do cadastro da máquina
            vehicle.status = VehicleStatus.AVAILABLE.value
            db.add(vehicle)

            # ✅ C. AVISA O KIOSK INSTANTANEAMENTE VIA WEBSOCKET!
            try:
                await manager.broadcast({
                    "type": "MACHINE_STATUS_CHANGED",
                    "machine_id": vehicle.id,
                    "status": "AVAILABLE"
                })
                print("📣 Kiosk avisado via WebSocket para remover a tela vermelha.")
            except Exception as e:
                print(f"⚠️ Erro ao tentar avisar o Kiosk: {e}")

    await db.commit()
    await db.refresh(db_obj)
    return db_obj

# 5. SERVIÇOS
@router.post("/requests/{request_id}/services", response_model=MaintenanceServiceItemPublic)
@router.post("/{request_id}/services", response_model=MaintenanceServiceItemPublic)
async def add_service_item(
    *,
    db: AsyncSession = Depends(deps.get_db),
    request_id: int,
    service_in: MaintenanceServiceItemCreate,
    current_user: User = Depends(deps.get_current_active_manager)
):
    req = await crud.maintenance.get_request(db, request_id=request_id, organization_id=current_user.organization_id)
    if not req: raise HTTPException(status_code=404, detail="Chamado não encontrado.")
    
    service_data = service_in.model_dump()
    
    db_service = MaintenanceServiceItem(
        **service_data, 
        maintenance_request_id=request_id, 
        added_by_id=current_user.id
    )
    
    db.add(db_service)
    
    new_cost = VehicleCost(
        description=f"Serviço: {service_in.description} (#{request_id})",
        amount=service_in.cost, date=datetime.now().date(), cost_type=CostType.MANUTENCAO,
        vehicle_id=req.vehicle_id, organization_id=current_user.organization_id
    )
    db.add(new_cost)
    await db.commit()
    await db.refresh(db_service)
    return db_service

# 6. COMENTÁRIOS
@router.get("/requests/{request_id}/comments", response_model=List[MaintenanceCommentPublic])
@router.get("/{request_id}/comments", response_model=List[MaintenanceCommentPublic])
async def read_comments_for_request(
    request_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    return await crud.maintenance_comment.get_comments_for_request(db=db, request_id=request_id, organization_id=current_user.organization_id)

@router.post("/requests/{request_id}/comments", response_model=MaintenanceCommentPublic, status_code=status.HTTP_201_CREATED)
@router.post("/{request_id}/comments", response_model=MaintenanceCommentPublic, status_code=status.HTTP_201_CREATED)
async def create_comment_for_request(
    *,
    db: AsyncSession = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    request_id: int,
    comment_in: MaintenanceCommentCreate,
    current_user: User = Depends(deps.get_current_active_user)
):
    try:
        comment = await crud.maintenance.create_comment(db, comment_in=comment_in, request_id=request_id, user_id=current_user.id, organization_id=current_user.organization_id)
        req = await crud.maintenance.get_request(db, request_id=request_id, organization_id=current_user.organization_id)
        
        await db.commit()
        await db.refresh(comment, ["user"])
        
        msg = f"Novo comentário de {current_user.full_name} no chamado #{request_id}."
        if req and req.reported_by_id and current_user.role != UserRole.DRIVER:
             background_tasks.add_task(crud.notification.create_notification, db=db, message=msg, notification_type=NotificationType.MAINTENANCE_REQUEST_NEW_COMMENT, organization_id=current_user.organization_id, user_id=req.reported_by_id, related_entity_type="maintenance_request", related_entity_id=request_id)
        
        return MaintenanceCommentPublic.model_validate(comment)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

# 7. UPLOAD
@router.post("/upload-file", response_model=dict)
async def upload_attachment_file(file: UploadFile = File(...), current_user: User = Depends(deps.get_current_active_manager)):
    ext = file.filename.split(".")[-1] if file.filename else ""
    fname = f"{uuid.uuid4()}.{ext}"
    loc = f"static/uploads/{fname}"
    with open(loc, "wb+") as f: shutil.copyfileobj(file.file, f)
    return {"file_url": f"/{loc}"}

# 8. TROCA DE PEÇAS
@router.post("/requests/{request_id}/replace-component", response_model=ReplaceComponentResponse)
@router.post("/{request_id}/replace-component", response_model=ReplaceComponentResponse)
async def replace_maintenance_component(
    *, db: AsyncSession = Depends(deps.get_db), background_tasks: BackgroundTasks,
    request_id: int, payload: ReplaceComponentPayload, current_user: User = Depends(deps.get_current_active_manager)
):
    try:
        log, comment, rep_id = await crud.maintenance.perform_component_replacement(db=db, request_id=request_id, payload=payload, user=current_user)
        await db.commit()

        # CORREÇÃO: Carregamento completo
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        stmt = select(MaintenancePartChange).where(MaintenancePartChange.id == log.id).options(
            selectinload(MaintenancePartChange.user),
            selectinload(MaintenancePartChange.component_removed).options(
                selectinload(VehicleComponent.part),
                selectinload(VehicleComponent.inventory_transaction).options(
                    selectinload(InventoryTransaction.item),
                    selectinload(InventoryTransaction.user)
                )
            ),
            selectinload(MaintenancePartChange.component_installed).options(
                selectinload(VehicleComponent.part),
                selectinload(VehicleComponent.inventory_transaction).options(
                    selectinload(InventoryTransaction.item),
                    selectinload(InventoryTransaction.user)
                )
            )
        )
        res = await db.execute(stmt)
        log = res.scalars().first()
        
        await db.refresh(comment, ["user"])
        
        return ReplaceComponentResponse(success=True, message="Substituição realizada.", part_change_log=log, new_comment=comment)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/requests/{request_id}/install-component", response_model=InstallComponentResponse)
@router.post("/{request_id}/install-component", response_model=InstallComponentResponse)
async def install_maintenance_component(
    *, db: AsyncSession = Depends(deps.get_db), background_tasks: BackgroundTasks,
    request_id: int, payload: InstallComponentPayload, current_user: User = Depends(deps.get_current_active_manager)
):
    try:
        log, comment, rep_id = await crud.maintenance.perform_new_installation(db=db, request_id=request_id, payload=payload, user=current_user)
        await db.commit()

        # CORREÇÃO: Carregamento completo com selectinload para evitar MissingGreenlet
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.maintenance_model import MaintenancePartChange, MaintenanceComment
        from app.models.vehicle_component_model import VehicleComponent
        from app.models.inventory_transaction_model import InventoryTransaction

        stmt = select(MaintenancePartChange).where(MaintenancePartChange.id == log.id).options(
            selectinload(MaintenancePartChange.user),
            selectinload(MaintenancePartChange.component_installed).options(
                selectinload(VehicleComponent.part),
                selectinload(VehicleComponent.inventory_transaction).options(
                    selectinload(InventoryTransaction.item),
                    selectinload(InventoryTransaction.user)
                )
            )
        )
        res = await db.execute(stmt)
        log = res.scalars().first()
        
        await db.refresh(comment, ["user"])

        return InstallComponentResponse(
            success=True, 
            message="Instalação realizada.", 
            part_change_log=log, 
            new_comment=comment
        )
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/part-changes/{change_id}/revert", response_model=MaintenanceCommentPublic)
async def revert_part_change(
    *, db: AsyncSession = Depends(deps.get_db), background_tasks: BackgroundTasks,
    change_id: int, current_user: User = Depends(deps.get_current_active_manager)
):
    try:
        log, comment, rep_id = await crud.maintenance.revert_part_change(db=db, change_id=change_id, user=current_user)
        await db.commit()
        return MaintenanceCommentPublic.model_validate(comment)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))