from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.audit_log_schema import AuditLogCreate
from app.crud import crud_audit_log
from app import crud
from app.schemas.user_schema import UserCreate, UserUpdate, UserPublic, UserStats, UserPasswordUpdate, UserNotificationPrefsUpdate
from app.core.security import verify_password
from app import deps
from app.models.user_model import User, UserRole
from sqlalchemy import select, update
from app.schemas.user_schema import UserDeviceToken
from app.services.fcm_service import send_push_notification
from pydantic import BaseModel
router = APIRouter()

@router.get("/by-badge/{badge}", response_model=UserPublic)
async def get_user_by_badge(
    badge: str,
    db: AsyncSession = Depends(deps.get_db),
    # current_user: User = Depends(deps.get_current_active_user) # Opcional: exige que o Kiosk esteja logado
):
    """
    Identifica um usuário pelo crachá (sem fazer login).
    Usado para trocar o operador da máquina dinamicamente.
    """
    # Busca exata pelo campo employee_id
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
    """Lista todos os utilizadores da organização do gestor."""
    users = await crud.user.get_multi_by_org(
        db, organization_id=current_user.organization_id, skip=skip, limit=limit
    )
    return users


@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED,
            dependencies=[Depends(deps.check_demo_limit("users"))])
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_active_manager),
):
    """
    Cria um novo utilizador DENTRO da organização do gestor logado.
    - Gestor Demo: Apenas Motoristas (DRIVER).
    - Gestor Ativo: Motoristas (DRIVER) ou Gestores (CLIENTE_ATIVO).
    """
    
    # Debug: Verifique no console se o role está chegando
    print(f"DEBUG CREATE USER: Role recebida no payload: {user_in.role}")

    # 1. Define o papel (Default é DRIVER se não for enviado)
    role_to_assign = user_in.role if user_in.role else UserRole.DRIVER

    # 2. Validações de Permissão
    if current_user.role == UserRole.CLIENTE_DEMO:
        if role_to_assign != UserRole.DRIVER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utilizadores em modo de demonstração só podem criar contas de Motorista."
            )
            
    elif current_user.role == UserRole.CLIENTE_ATIVO:
        # Permite criar Motorista OU outro Gestor (Cliente Ativo)
        if role_to_assign not in [UserRole.DRIVER, UserRole.CLIENTE_ATIVO]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só tem permissão para criar Motoristas ou outros Gestores."
            )
    
    # Bloqueia criação de ADMIN por vias normais
    if role_to_assign == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Não autorizado a criar administradores.")

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

    return new_user
@router.put("/me", response_model=UserPublic)
async def update_user_me(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """Permite que o usuário atualize seus próprios dados básicos (foto, nome, telefone)."""
    
    # 1. Converter para dicionário, ignorando campos não enviados
    update_data = user_in.model_dump(exclude_unset=True)
    
    # 2. Remover campos sensíveis do dicionário (para que não sejam alterados)
    # Se 'role' estiver presente, o .pop vai remover. Se não estiver, não faz nada.
    update_data.pop("role", None)
    update_data.pop("is_active", None)
    update_data.pop("organization_id", None)
    update_data.pop("password", None)

    # 3. Passar o dicionário limpo para o CRUD
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
        raise HTTPException(status_code=400, detail="A senha atual está incorreta.")
    
    updated_user = await crud.user.update_password(
        db, db_user=current_user, new_password=password_data.new_password
    )
    return updated_user

@router.put("/me/password", response_model=UserPublic)
async def update_current_user_password(
    *,
    db: AsyncSession = Depends(deps.get_db),
    password_data: UserPasswordUpdate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """Atualiza a senha do utilizador logado."""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha atual está incorreta."
        )
    
    updated_user = await crud.user.update_password(
        db, db_user=current_user, new_password=password_data.new_password
    )
    return updated_user

@router.put("/me/preferences", response_model=UserPublic)
async def update_current_user_preferences(
    *,
    db: AsyncSession = Depends(deps.get_db),
    prefs_in: UserNotificationPrefsUpdate,
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Atualiza as preferências de notificação do utilizador logado.
    """
    update_data = UserUpdate(**prefs_in.model_dump())
    updated_user = await crud.user.update(db=db, db_user=current_user, user_in=update_data)
    return updated_user

@router.get("/me", response_model=UserPublic)
async def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
):
    """Retorna os dados do utilizador logado."""
    return current_user

@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_manager),
):
    """Busca os dados de um único utilizador da organização do gestor."""
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
    """Atualiza um utilizador da organização do gestor."""
    user_to_update = await crud.user.get(
        db, id=user_id, organization_id=current_user.organization_id
    )
    if not user_to_update:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")

    # Lógica corrigida para alteração de papéis
    if user_in.role is not None and user_in.role != user_to_update.role:
        # Se for ADMIN, pode tudo
        if current_user.role == UserRole.ADMIN:
            pass
        # Se for CLIENTE_ATIVO, pode alterar entre DRIVER e CLIENTE_ATIVO
        elif current_user.role == UserRole.CLIENTE_ATIVO:
            if user_in.role not in [UserRole.DRIVER, UserRole.CLIENTE_ATIVO]:
                raise HTTPException(status_code=403, detail="Você não pode atribuir esse papel.")
        # Outros (como DEMO) não podem alterar papel
        else:
            raise HTTPException(status_code=403, detail="Você não tem permissão para alterar o papel de um utilizador.")

    updated_user = await crud.user.update(db=db, db_user=user_to_update, user_in=user_in)
    return updated_user


@router.delete("/{user_id}", response_model=UserPublic)
async def delete_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_manager),
):
    """Exclui um utilizador da organização do gestor."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode excluir a sua própria conta de gestor.",
        )
    
    user_to_delete = await crud.user.get(
        db, id=user_id, organization_id=current_user.organization_id
    )
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
    
    # Validamos e convertemos para o schema Pydantic ANTES de deletar.
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
    """
    Retorna as estatísticas de um utilizador.
    - Gestores podem ver as estatísticas de qualquer utilizador na sua organização.
    - Motoristas podem ver apenas as suas próprias estatísticas.
    """
    # --- CORREÇÃO AQUI: Adicionado UserRole.ADMIN na lista de permissões ---
    is_manager = current_user.role in [UserRole.CLIENTE_ATIVO, UserRole.CLIENTE_DEMO, UserRole.ADMIN]
    is_driver_requesting_own_stats = (current_user.role == UserRole.DRIVER and current_user.id == user_id)

    if not is_manager and not is_driver_requesting_own_stats:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para ver estas estatísticas."
        )

    # Garante que o usuário solicitado pertence à mesma organização
    target_user = await crud.user.get(db, id=user_id)
    
    # Se o usuário alvo não existe ou não pertence à mesma organização
    if not target_user or target_user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado para gerar estatísticas.")

    stats = await crud.user.get_user_stats(
        db, user_id=user_id, organization_id=current_user.organization_id
    )
    if not stats:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado para gerar estatísticas.")
    
    return stats
    
@router.post("/me/device-token")
async def register_device_token(
    token_in: UserDeviceToken,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Salva o token do celular do usuário para enviar notificações."""
    current_user.device_token = token_in.token
    db.add(current_user)
    await db.commit()
    
    # Opcional: Envia uma notificação de boas-vindas para testar
    # send_push_notification(token_in.token, "Conectado!", "Seu celular está pronto para receber alertas.")
    
    return {"status": "success"}

class DeviceTokenSchema(BaseModel):
    token: str

@router.post("/me/device-token")
async def update_device_token(
    payload: DeviceTokenSchema,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Salva o token do Firebase do dispositivo atual.
    IMPORTANTE: Remove este token de qualquer outro usuário para evitar notificações duplicadas.
    """
    
    # 1. A REGRA DO HIGHLANDER: "Só pode haver um"
    # Remove este token de qualquer usuário que NÃO seja o atual.
    # Isso resolve o problema de logar com Admin e depois com Manutenção no mesmo tablet.
    stmt = update(User).where(
        User.device_token == payload.token,
        User.id != current_user.id
    ).values(device_token=None)
    
    await db.execute(stmt)
    
    # 2. Salva no usuário atual
    current_user.device_token = payload.token
    db.add(current_user)
    
    await db.commit()
    
    print(f"📲 Token vinculado ao usuário {current_user.email} (e removido de outros).")
    return {"status": "updated", "message": "Token vinculado e limpo de sessões anteriores."}