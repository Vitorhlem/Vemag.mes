from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import crud, deps
from app.models.user_model import User
from app.schemas.machine_component_schema import MachineComponentCreate, MachineComponentPublic

router = APIRouter()


@router.get("/machines/{machine_id}/components", response_model=List[MachineComponentPublic])
async def read_components_for_machine(
    machine_id: int,
    db: AsyncSession = Depends(deps.get_db),
    # --- CORREÇÃO AQUI ---
    # Alterado de get_current_active_manager para get_current_active_user
    # Isso permite que Motoristas vejam os componentes (necessário para o fluxo de manutenção)
    current_user: User = Depends(deps.get_current_active_user),
    # ---------------------
):
    """
    Busca o histórico de componentes instalados em um veículo.
    Acessível por Gestores e Motoristas.
    """
    machine = await crud.machine.get(db, machine_id=machine_id, organization_id=current_user.organization_id)
    if not machine:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    components = await crud.machine_component.get_components_by_machine(db=db, machine_id=machine_id)
    return components


@router.post("/machines/{machine_id}/components", response_model=MachineComponentPublic, status_code=status.HTTP_201_CREATED)
async def install_machine_component(
    machine_id: int,
    *,
    db: AsyncSession = Depends(deps.get_db),
    obj_in: MachineComponentCreate,
    current_user: User = Depends(deps.get_current_active_manager),
):
    """
    Instala um novo componente em um veículo.
    (CORRIGIDO com Commit-e-Refetch)
    """
    try:
        # 1. CRUD (NÃO FAZ COMMIT)
        new_component = await crud.machine_component.install_component(
            db=db,
            machine_id=machine_id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            obj_in=obj_in
        )
        component_id = new_component.id
        
        # 2. ENDPOINT FAZ COMMIT
        await db.commit()
        
        # 3. Recarregamos o componente com todos os dados para a API
        reloaded_component = await crud.machine_component.get_component_for_api(
            db=db, component_id=component_id
        )
        return reloaded_component
        
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao instalar componente: {e}")


@router.put("/machine-components/{component_id}/discard", response_model=MachineComponentPublic)
async def discard_machine_component(
    component_id: int,
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_manager),
):
    """
    Marca um componente como 'descartado' (Fim de Vida).
    (CORRIGIDO com Commit-e-Refetch)
    """
    try:
        # 1. CRUD (NÃO FAZ COMMIT)
        discarded_component = await crud.machine_component.discard_component(
            db=db,
            component_id=component_id,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # 2. ENDPOINT FAZ COMMIT
        await db.commit()
        
        # 3. Recarregamos o componente com todos os dados para a API
        reloaded_component = await crud.machine_component.get_component_for_api(
            db=db, component_id=discarded_component.id
        )
        return reloaded_component

    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao descartar componente: {e}")