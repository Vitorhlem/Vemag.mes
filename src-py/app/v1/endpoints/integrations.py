from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app import deps
from app.services.sap_sync import SAPIntegrationService
from app.models.user_model import User
from app.services.rm_sync import RMIntegrationService
router = APIRouter()

@router.post("/sync/sap")
async def trigger_sap_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Dispara a sincronização com o SAP em segundo plano.
    """
    # Instancia o serviço passando o ID da organização do usuário logado
    sap_service = SAPIntegrationService(db, organization_id=current_user.organization_id)
    
    # Adiciona nas tarefas de fundo para não travar a API
    background_tasks.add_task(run_sync_task, sap_service)
    
    return {"message": "Sincronização com SAP iniciada em background."}

async def run_sync_task(service: SAPIntegrationService):
    try:
        await service.sync_machines()
        await service.sync_operators()
    finally:
        await service.close()

@router.post("/sync/rm")
async def trigger_rm_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Sincroniza Colaboradores do RM TOTVS (Tabela PFUNC).
    """
    rm_service = RMIntegrationService(db, organization_id=current_user.organization_id)
    
    # Roda em background
    background_tasks.add_task(rm_service.sync_employees)
    
    return {"message": "Sincronização com RM TOTVS iniciada."}