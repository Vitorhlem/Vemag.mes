from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.audit_log_schema import AuditLogCreate
from app.crud import crud_audit_log
from app import crud
from app.schemas.user_schema import UserCreate, UserUpdate, UserPublic, UserStats, UserPasswordUpdate, UserDeviceToken
from app.core.security import verify_password
from app import deps
from app.models.user_model import User, UserRole
from sqlalchemy import select, update
from pydantic import BaseModel

router = APIRouter()

@router.get("/by-badge/{badge}", response_model=UserPublic)
async def get_user_by_badge(
    badge: str,
    db: AsyncSession = Depends(deps.get_db),
):
    query = select(User).where(User.employee_id == badge)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Crachá não encontrado")
        
    return user


@router.get("/", response_model=List[UserPublic])
async def read_users(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_manager),
):
    users = await crud.user.get_multi_by_org(
        db, organization_id=current_user.organization_id, skip=skip, limit=limit
    )
    return users


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_active_manager),
):
    """
    Cria um novo utilizador DENTRO da organização.
    """
    
    # 1. Define o papel (Default é OPERATOR)
    role_to_assign = user_in.role if user_in.role else UserRole.OPERATOR

    # 2. Validação de Hierarquia
    # Apenas ADMIN pode criar outro ADMIN ou MANAGER
    if role_to_assign in [UserRole.ADMIN, UserRole.MANAGER] and current_user.role != UserRole.ADMIN:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas Administradores podem criar outros gestores."
        )

    # 3. Verifica duplicidade de e-mail
    user = await crud.user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O e-mail fornecido já está registado no sistema.",
        )
    
    # 4. Criação
    new_user = await crud.user.create(
        db=db, user_in=user_in, 
        organization_id=current_user.organization_id,
        role=role_to_assign
    )

    # --- LOG DE AUDITORIA ---
    try:
        await crud_audit_log.create(db=db, log_in=AuditLogCreate(
            action="CREATE",
            resource_type="Usúarios",
            resource_id=str(new_user.id),
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            details={"email": new_user.email, "role": new_user.role}
        ))
        await db.commit() 
    except Exception as e:
        print(f"Falha ao criar log de auditoria: {e}")

    return new_user


@router.put("/me", response_model=UserPublic)
async def update_user_me(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
):
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Remover campos sensíveis
    update_data.pop("role", None)
    update_data.pop("is_active", None)
    update_data.pop("organization_id", None)
    update_data.pop("password", None)

    updated_user = await crud.user.update(db=db, db_user=current_user, user_in=update_data)
    return updated_user


@router.put("/me/password", response_model=UserPublic)
async def update_current_user_password(
    *,
    db: AsyncSession = Depends(deps.get_db),
    password_data: UserPasswordUpdate,
    current_user: User = Depends(deps.get_current_active_user),
):
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha atual está incorreta."
        )
    
    updated_user = await crud.user.update_password(
        db, db_user=current_user, new_password=password_data.new_password
    )
    return updated_user


@router.get("/me", response_model=UserPublic)
async def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
):
    return current_user


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_manager),
):
    user = await crud.user.get(
        db, id=user_id, organization_id=current_user.organization_id
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador não encontrado.",
        )
    return user


@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_manager),
):
    user_to_update = await crud.user.get(
        db, id=user_id, organization_id=current_user.organization_id
    )
    if not user_to_update:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")

    # Proteção de hierarquia
    if user_in.role is not None and user_in.role != user_to_update.role:
        if current_user.role != UserRole.ADMIN:
             raise HTTPException(status_code=403, detail="Apenas Administradores podem alterar cargos.")

    updated_user = await crud.user.update(db=db, db_user=user_to_update, user_in=user_in)
    return updated_user


@router.delete("/{user_id}", response_model=UserPublic)
async def delete_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_manager),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode excluir a sua própria conta.",
        )
    
    user_to_delete = await crud.user.get(
        db, id=user_id, organization_id=current_user.organization_id
    )
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
    
    user_response = UserPublic.model_validate(user_to_delete)
    
    await crud.user.remove(db=db, db_user=user_to_delete)

    try:
        await crud_audit_log.create(db=db, log_in=AuditLogCreate(
            action="DELETE",
            resource_type="Usúarios",
            resource_id=str(user_id),
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            details={"deleted_user_name": user_to_delete.full_name}
        ))
        await db.commit()
    except Exception as e:
        print(f"Falha ao criar log de auditoria: {e}")
    
    return user_response


@router.get("/{user_id}/stats", response_model=UserStats)
async def read_user_stats(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    # Permite que gestores vejam de todos e operadores vejam o seu próprio
    is_manager = current_user.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.PCP]
    is_self = (current_user.id == user_id)

    if not is_manager and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para ver estas estatísticas."
        )

    target_user = await crud.user.get(db, id=user_id)
    
    if not target_user or target_user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")

    stats = await crud.user.get_user_stats(
        db, user_id=user_id, organization_id=current_user.organization_id
    )
    if not stats:
        # Retorna zerado se não tiver stats
        return UserStats(
            primary_metric_label="N/A", primary_metric_value=0, primary_metric_unit="-", maintenance_requests_count=0
        )
    
    return stats


class DeviceTokenSchema(BaseModel):
    token: str

@router.post("/me/device-token")
async def update_device_token(
    payload: DeviceTokenSchema,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    # Remove de outros users
    stmt = update(User).where(
        User.device_token == payload.token,
        User.id != current_user.id
    ).values(device_token=None)
    
    await db.execute(stmt)
    
    # Salva no atual
    current_user.device_token = payload.token
    db.add(current_user)
    
    await db.commit()
    
    return {"status": "updated", "message": "Token vinculado com sucesso."}