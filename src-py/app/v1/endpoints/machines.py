from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from app.schemas.audit_log_schema import AuditLogCreate
from app.crud import crud_audit_log
from app import crud, deps
from app.models.user_model import User
from sqlalchemy.exc import IntegrityError

from app.schemas.machine_schema import (
    MachineCreate,
    MachineUpdate,
    MachinePublic,
    MachineListResponse
)
from app.schemas.inventory_transaction_schema import TransactionPublic

router = APIRouter()

# --- NOVO SCHEMA PARA ATUALIZAÇÃO DO EIXO ---
class AxleConfigUpdate(BaseModel):
    axle_configuration: str

@router.get("/", response_model=MachineListResponse)
async def read_machines(
    db: AsyncSession = Depends(deps.get_db),
    page: int = 1,
    rowsPerPage: int = 8,
    search: str | None = None,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Lista os veículos da organização com paginação e busca.
    """
    skip = (page - 1) * rowsPerPage

    machines = await crud.machine.get_multi_by_org(
        db,
        organization_id=current_user.organization_id,
        skip=skip,
        limit=rowsPerPage,
        search=search
    )
    total_items = await crud.machine.count_by_org(
        db,
        organization_id=current_user.organization_id,
        search=search
    )

    return {"machines": machines, "total_items": total_items}


@router.get("/{machine_id}", response_model=MachinePublic)
async def read_machine_by_id(
    *,
    db: AsyncSession = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Busca um único veículo pelo ID.
    """
    machine = await crud.machine.get(
        db, machine_id=machine_id, organization_id=current_user.organization_id
    )
    if not machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")
    return machine


@router.get("/{machine_id}/inventory-history", response_model=List[TransactionPublic])
async def read_machine_inventory_history(
    *,
    db: AsyncSession = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Retorna o histórico de todas as movimentações de peças/inventário
    associadas a um veículo específico.
    """
    machine = await crud.machine.get(db, machine_id=machine_id, organization_id=current_user.organization_id)
    if not machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")

    history = await crud.inventory_transaction.get_transactions_by_machine_id(db, machine_id=machine_id)
    return history


# --- CORREÇÃO: Removido dependencies=[Depends(deps.machine("machines"))] ---
@router.post("/", response_model=MachinePublic, status_code=status.HTTP_201_CREATED)
async def create_machine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    machine_in: MachineCreate,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """Cria um novo veículo para a organização do gestor logado."""
    try:
        machine = await crud.machine.create_with_owner(
            db=db, obj_in=machine_in, organization_id=current_user.organization_id
        )

        try:
            details_data = {"plate": machine.license_plate, "model": machine.model}
            
            await crud_audit_log.create(db=db, log_in=AuditLogCreate(
                action="CREATE", resource_type="Máquinario", resource_id=str(machine.id),
                user_id=current_user.id, organization_id=current_user.organization_id,
                details=jsonable_encoder(details_data)
            ))
            await db.commit()
        except Exception as e:
            print(f"Erro auditoria: {e}")

        return machine
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um veículo com esta placa ou identificador já existe na sua organização.",
        )


@router.put("/{machine_id}", response_model=MachinePublic)
async def update_machine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    machine_id: int,
    machine_in: MachineUpdate,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """
    Atualiza um veículo.
    """
    db_machine = await crud.machine.get(
        db, machine_id=machine_id, organization_id=current_user.organization_id
    )
    if not db_machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")

    updated_machine = await crud.machine.update(db=db, db_machine=db_machine, machine_in=machine_in)

    try:
        log_details = jsonable_encoder(machine_in.model_dump(exclude_unset=True))
        
        await crud_audit_log.create(db=db, log_in=AuditLogCreate(
            action="UPDATE", resource_type="Máquinario", resource_id=str(updated_machine.id),
            user_id=current_user.id, organization_id=current_user.organization_id,
            details={"updates": log_details}
        ))
        await db.commit()
    except Exception as e:
        print(f"Erro auditoria: {e}")

    return updated_machine


@router.patch("/{machine_id}/axle-config", response_model=MachinePublic)
async def update_machine_axle_config(
    *,
    db: AsyncSession = Depends(deps.get_db),
    machine_id: int,
    config_in: AxleConfigUpdate,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """
    Atualiza a configuração de eixos de um veículo.
    """
    db_machine = await crud.machine.get(
        db, machine_id=machine_id, organization_id=current_user.organization_id
    )
    if not db_machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")

    db_machine.axle_configuration = config_in.axle_configuration
    db.add(db_machine)
    await db.commit()
    await db.refresh(db_machine)
    return db_machine


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine(
    *,
    db: AsyncSession = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(deps.get_current_active_manager)
):
    """
    Exclui um veículo.
    """
    db_machine = await crud.machine.get(
        db, machine_id=machine_id, organization_id=current_user.organization_id
    )
    if not db_machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")

    await crud.machine.remove(db=db, db_machine=db_machine)

    try:
        await crud_audit_log.create(db=db, log_in=AuditLogCreate(
            action="DELETE", resource_type="Máquinario", resource_id=str(machine_id),
            user_id=current_user.id, organization_id=current_user.organization_id,
            details={"deleted_plate": db_machine.license_plate}
        ))
        await db.commit()
    except Exception as e:
        print(f"Erro auditoria: {e}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)