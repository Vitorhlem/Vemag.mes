from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import crud, deps
from app.models.user_model import User
from app.schemas.machine_cost_schema import MachineCostCreate, MachineCostPublic

router = APIRouter()


@router.get("/", response_model=List[MachineCostPublic])
async def read_machine_costs(
    *,
    db: AsyncSession = Depends(deps.get_db),
    machine_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """
    Lista todos os custos associados a uma máquina específica.
    """
    machine = await crud.machine.get(db, machine_id=machine_id, organization_id=current_user.organization_id)
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Máquina não encontrada nesta organização."
        )
    
    # Nota: Certifique-se que o CRUD machine_cost foi atualizado para procurar por machine_id
    costs = await crud.machine_cost.get_costs_by_machine(
        db, machine_id=machine_id, skip=skip, limit=limit
    )
    return costs


@router.post("/", response_model=MachineCostPublic, status_code=status.HTTP_201_CREATED)
async def create_machine_cost(
    *,
    db: AsyncSession = Depends(deps.get_db),
    machine_id: int,
    cost_in: MachineCostCreate,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """
    Cria um novo registo de custo para uma máquina específica.
    """
    # 1. Validação da Máquina
    machine = await crud.machine.get(db, machine_id=machine_id, organization_id=current_user.organization_id)
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Máquina não encontrada nesta organização."
        )

    # 2. Criação do Custo
    cost = await crud.machine_cost.create_cost(
        db, obj_in=cost_in, machine_id=machine_id, organization_id=current_user.organization_id
    )
    return cost