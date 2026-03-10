from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.notification_model import Notification, NotificationType
from app.models.user_model import User, UserRole
from app.models.machine_model import Machine
from app.models.document_model import Document

# --- FUNÇÃO DE CRIAÇÃO ATUALIZADA ---
async def create_notification(
    db: AsyncSession,
    *,
    message: str,
    notification_type: NotificationType,
    organization_id: int,
    user_id: int | None = None,
    send_to_managers: bool = False,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
    related_machine_id: int | None = None # Nome correto do parâmetro
):
    """
    Cria uma notificação para um usuário específico OU para todos os gestores.
    """
    target_user_ids = []
    if user_id:
        target_user_ids.append(user_id)
        
    if send_to_managers:
        # --- CORREÇÃO DE CARGOS ---
        # Removido CLIENTE_ATIVO/DEMO. Usamos os novos cargos de gestão.
        manager_roles = [UserRole.ADMIN, UserRole.MANAGER, UserRole.PCP, UserRole.MAINTENANCE]
        
        manager_stmt = select(User.id).where(
            User.organization_id == organization_id,
            User.role.in_(manager_roles),
            User.is_active == True
        )
        manager_ids = (await db.execute(manager_stmt)).scalars().all()
        target_user_ids.extend(manager_ids)

    unique_user_ids = set(target_user_ids)

    for uid in unique_user_ids:
        new_notification = Notification(
            organization_id=organization_id,
            user_id=uid,
            message=message,
            notification_type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            # --- CORREÇÃO DO ERRO NameError ---
            related_machine_id=related_machine_id 
        )
        db.add(new_notification)
        
    await db.commit()
# --- FIM DA ATUALIZAÇÃO ---


async def get_notifications_for_user(db: AsyncSession, *, user_id: int, organization_id: int) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id, Notification.organization_id == organization_id)
        .order_by(Notification.created_at.desc())
        .options(selectinload(Notification.machine))
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_unread_notifications_count(db: AsyncSession, *, user_id: int, organization_id: int) -> int:
    stmt = select(func.count(Notification.id)).where(
        Notification.user_id == user_id,
        Notification.is_read == False,
        Notification.organization_id == organization_id
    )
    result = await db.execute(stmt)
    return result.scalar_one()

async def mark_notification_as_read(db: AsyncSession, *, notification_id: int, user_id: int, organization_id: int) -> Notification | None:
    stmt = (
        select(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.organization_id == organization_id
        )
        .options(selectinload(Notification.user), selectinload(Notification.machine)) 
    )
    notification = await db.scalar(stmt)
    
    if notification:
        notification.is_read = True
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
    return notification

async def run_system_checks_for_organization(db: AsyncSession, *, organization_id: int):
    print(f"A verificar alertas para a Organização ID: {organization_id}")
    
    # 1. Manutenção por Data
    date_threshold = datetime.utcnow().date() + timedelta(days=14)
    machines_due_date_stmt = select(Machine).where(
        Machine.organization_id == organization_id,
        Machine.next_maintenance_date != None,
        Machine.next_maintenance_date <= date_threshold
    )
    for machine in (await db.execute(machines_due_date_stmt)).scalars().all():
        message = f"Manutenção agendada para {machine.brand} {machine.model} em {machine.next_maintenance_date.strftime('%d/%m/%Y')}."
        # Correção: related_machine_id
        await create_notification(db, message=message, notification_type=NotificationType.MAINTENANCE_DUE_DATE, organization_id=organization_id, send_to_managers=True, related_machine_id=machine.id)

    # 3. Documentos a Vencer
    doc_date_threshold = datetime.utcnow().date() + timedelta(days=30)
    docs_expiring_stmt = select(Document).where(
        Document.organization_id == organization_id,
        Document.expiry_date != None,
        Document.expiry_date <= doc_date_threshold
    ).options(selectinload(Document.machine), selectinload(Document.operator))
    
    for doc in (await db.execute(docs_expiring_stmt)).scalars().all():
        target_name = doc.machine.model if doc.machine else (doc.operator.full_name if doc.operator else "Desconhecido")
        machine_id = doc.machine.id if doc.machine else None
        
        message = f"O documento '{doc.document_type}' de {target_name} vence em {doc.expiry_date.strftime('%d/%m/%Y')}."
        
        # Correção: related_machine_id (passando ID e não objeto)
        await create_notification(
            db, 
            message=message, 
            notification_type=NotificationType.DOCUMENT_EXPIRING, 
            organization_id=organization_id, 
            send_to_managers=True, 
            related_entity_type="document", 
            related_entity_id=doc.id, 
            related_machine_id=machine_id
        )
        
    print(f"Verificação de alertas concluída para a Organização ID: {organization_id}")