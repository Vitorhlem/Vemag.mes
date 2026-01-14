from fastapi import APIRouter, Depends, HTTPException, Response, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import uuid
import shutil

from app import crud, deps
from app.core.config import settings 
from app.core.email_utils import send_email 
from app.models.user_model import User, UserRole

# Schemas
from app.schemas.maintenance_schema import (
    MaintenanceRequestPublic, MaintenanceRequestCreate, MaintenanceRequestUpdate,
    MaintenanceCommentPublic, MaintenanceCommentCreate,
    ReplaceComponentPayload, ReplaceComponentResponse, InstallComponentResponse,
    InstallComponentPayload,
    MaintenanceServiceItemCreate, MaintenanceServiceItemPublic
)
from app.schemas.audit_log_schema import AuditLogCreate

# Models e CRUDs
from app.crud import crud_audit_log
from app.crud.crud_demo_usage import demo_usage as demo_usage_crud
from app.models.maintenance_model import MaintenanceServiceItem 
from app.models.vehicle_cost_model import VehicleCost, CostType 
from app.models.notification_model import NotificationType

# --- IMPORT IMPORTANTE: Vehicle e Status ---
try:
    from app.models.vehicle_model import Vehicle, VehicleStatus
except ImportError:
    from app.models.vehicle import Vehicle, VehicleStatus

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
# ROTAS (HÍBRIDAS: Aceitam /requests e /raiz para compatibilidade)
# ============================================================================

# 1. CRIAR CHAMADO
# Quando cria a O.M., a máquina VAI para MANUTENÇÃO.
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
            print(f"[DEBUG] O.M. Aberta. Bloqueando veículo {vehicle.id} para MAINTENANCE.")
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

# 4. ATUALIZAR STATUS (AQUI OCORRE A LIBERAÇÃO AUTOMÁTICA)
@router.put("/requests/{request_id}/status", response_model=MaintenanceRequestPublic)
@router.put("/{request_id}/status", response_model=MaintenanceRequestPublic)
async def update_request_status(
    *,
    db: AsyncSession = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    request_id: int,
    update_data: MaintenanceRequestUpdate,
    current_user: User = Depends(deps.get_current_active_manager)
):
    db_obj = await crud.maintenance.get_request(db, request_id=request_id, organization_id=current_user.organization_id)
    if not db_obj: raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    
    updated = await crud.maintenance.update_request_status(db=db, db_obj=db_obj, update_data=update_data, manager_id=current_user.id)
    
    # --- LÓGICA DE LIBERAÇÃO DA MÁQUINA ---
    # Verifica se o novo status significa que a O.M. foi encerrada
    new_status_val = str(updated.status.value if hasattr(updated.status, 'value') else updated.status).upper()
    
    # Lista de status que liberam a máquina
    finished_statuses = ["COMPLETED", "CONCLUIDO", "CLOSED", "FECHADO", "CANCELED", "CANCELADO", "REJECTED"]
    
    if any(s in new_status_val for s in finished_statuses):
        vehicle = await db.get(Vehicle, db_obj.vehicle_id)
        if vehicle:
            # Verifica se o status atual da máquina é manutenção/quebrada
            v_status = str(vehicle.status.value if hasattr(vehicle.status, 'value') else vehicle.status).upper()
            
            if "MANUTEN" in v_status or "MAINTENANCE" in v_status:
                print(f"[DEBUG] O.M. #{request_id} Finalizada ({new_status_val}). Liberando máquina {vehicle.id} para AVAILABLE.")
                # LIBERA A MÁQUINA
                vehicle.status = VehicleStatus.AVAILABLE.value
                db.add(vehicle)
    # --------------------------------------

    response = MaintenanceRequestPublic.model_validate(updated)
    
    msg = f"Status do chamado #{updated.id} atualizado para: {updated.status.value}."
    if updated.reported_by_id:
        background_tasks.add_task(crud.notification.create_notification, db=db, message=msg, notification_type=NotificationType.MAINTENANCE_REQUEST_STATUS_UPDATE, user_id=updated.reported_by_id, organization_id=current_user.organization_id, related_entity_type="maintenance_request", related_entity_id=updated.id)
    
    await crud_audit_log.create(db=db, log_in=AuditLogCreate(
        action="UPDATE", resource_type="Chamado de Manutenção", resource_id=str(updated.id),
        user_id=current_user.id, organization_id=current_user.organization_id,
        details={"new_status": update_data.status}
    ))
    
    await db.commit()
    return response

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
            
    db_service = MaintenanceServiceItem(**service_in.model_dump(), maintenance_request_id=request_id, added_by_id=current_user.id)
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
        await db.refresh(log, ["user", "component_removed", "component_installed"])
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
        await db.refresh(log, ["user", "component_installed"])
        return InstallComponentResponse(success=True, message="Instalação realizada.", part_change_log=log, new_comment=comment)
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