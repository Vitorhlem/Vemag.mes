from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from sqlalchemy import select, func, desc, or_
from app import crud, deps
from sqlalchemy.orm import selectinload

# Imports dos Modelos MES
from app.models.user_model import User, UserRole
from app.models.machine_model import Machine, MachineStatus
from app.models.maintenance_model import MaintenanceRequest, MaintenanceStatus
from app.models.machine_cost_model import MachineCost # A classe chama-se MachineCost no ficheiro

# Imports dos Schemas
from app.schemas.dashboard_schema import ManagerDashboardResponse

router = APIRouter()

# --- FUNÇÃO HELPER PARA LIDAR COM O FILTRO DE PERÍODO ---
def _get_start_date_from_period(period: str) -> date:
    """Converte uma string de período ('last_7_days', etc.) em uma data de início."""
    today = datetime.utcnow().date()
    if period == "last_7_days":
        return today - timedelta(days=7)
    if period == "this_month":
        return today.replace(day=1)
    # Padrão para 'last_30_days'
    return today - timedelta(days=30)


# --- ENDPOINT PARA O DASHBOARD DO GESTOR ---
@router.get(
    "/manager",
    response_model=ManagerDashboardResponse,
    summary="Obtém os dados completos para o dashboard do gestor",
)
async def read_manager_dashboard(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager),
    period: str = "last_30_days"
):
    """
    Dashboard principal do MES.
    Calcula KPIs em tempo real baseados nas Máquinas e Manutenções.
    """
    
    # 1. VALIDAÇÃO DE ACESSO (Novos Perfis MES)
    allowed_roles = [
        UserRole.ADMIN, 
        UserRole.MANAGER,
        UserRole.PCP, 
        UserRole.MAINTENANCE,
        UserRole.QUALITY,
        UserRole.LOGISTICS
    ]
    
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso não autorizado a este dashboard.",
        )

    org_id = current_user.organization_id
    start_date = _get_start_date_from_period(period)

    # ---------------------------------------------------------
    # 2. CÁLCULO DOS KPIS DE MÁQUINAS
    # ---------------------------------------------------------
    query_machines = select(Machine).where(Machine.organization_id == org_id)
    machines = (await db.execute(query_machines)).scalars().all()

    total_machines = len(machines)
    
    available_count = 0
    in_use_count = 0
    maintenance_count = 0

    for m in machines:
        st = str(m.status).upper()
        if st in ["DISPONÍVEL", "AVAILABLE", "PARADA", "IDLE"]:
            available_count += 1
        elif st in ["EM USO", "IN_USE", "RODANDO", "RUNNING", "SETUP", "PRODUÇÃO AUTÔNOMA"]:
            in_use_count += 1
        elif st in ["MANUTENÇÃO", "MAINTENANCE", "EM MANUTENÇÃO"]:
            maintenance_count += 1

    kpis = {
        "total_machines": total_machines,
        "available_machines": available_count,
        "in_use_machines": in_use_count,
        "maintenance_machines": maintenance_count,
        "total_distance": 0.0, # Legado
        "total_fuel": 0.0      # Legado
    }

    # ---------------------------------------------------------
    # 3. CUSTOS POR CATEGORIA (CORRIGIDO: cost_type e amount)
    # ---------------------------------------------------------
    costs_query = (
        select(MachineCost.cost_type, func.sum(MachineCost.amount))
        .where(
            MachineCost.organization_id == org_id,
            MachineCost.date >= start_date
        )
        .group_by(MachineCost.cost_type)
    )
    costs_result = (await db.execute(costs_query)).all()
    
    # CORREÇÃO: Transformar em lista de dicionários para o Pydantic validar como List[CostByCategory]
    costs_by_category = [
        {"category": row[0], "value": row[1]} 
        for row in costs_result
    ]

    # ---------------------------------------------------------
    # 5. PRÓXIMAS MANUTENÇÕES
    # ---------------------------------------------------------
    maint_query = (
        select(MaintenanceRequest)
        .options(selectinload(MaintenanceRequest.machine))
        .where(
            MaintenanceRequest.organization_id == org_id,
            MaintenanceRequest.status.in_([MaintenanceStatus.PENDENTE, MaintenanceStatus.EM_ANDAMENTO])
        )
        .order_by(MaintenanceRequest.created_at.desc())
        .limit(5)
    )
    maint_objs = (await db.execute(maint_query)).scalars().all()

    upcoming_maintenances = []
    for m in maint_objs:
        upcoming_maintenances.append({
            "id": m.id,
            "machine_name": f"{m.machine.brand} {m.machine.model}" if m.machine else "Desconhecida",
            "description": m.problem_description,
            "date": m.created_at.date(), 
            "status": m.status
        })

    # ---------------------------------------------------------
    # 6. KPIS DE EFICIÊNCIA (Placeholder)
    # ---------------------------------------------------------
    efficiency_kpis = {
        "availability": 0.0,
        "performance": 0.0,
        "quality": 0.0,
        "oee": 0.0
    }

    # ---------------------------------------------------------
    # 7. RETORNO DA RESPOSTA
    # ---------------------------------------------------------
    return ManagerDashboardResponse(
        kpis=kpis,
        efficiency_kpis=efficiency_kpis,
        costs_by_category=costs_by_category,
        upcoming_maintenances=upcoming_maintenances,
    )