# Em src-py/app/tasks/notification_tasks.py
import asyncio
from app.core.celery_app import celery_app
# Verifique o nome correto aqui: pode ser SessionLocal ou async_session
from app.db.session import SessionLocal 
from app.core.websocket_manager import manager
from app.models.notification_model import NotificationType

def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

@celery_app.task(name="dispatch_notification")
def dispatch_notification(message, notification_type, organization_id, **kwargs):
    async def _logic():
        from app import crud 
        async with SessionLocal() as db:
            await crud.notification.create_notification(
                db,
                message=message,
                notification_type=NotificationType(notification_type),
                organization_id=organization_id,
                **kwargs
            )
            # PRINT DE DEBUG
            print(f"📣 [WS BROADCAST] Notificando Org ID: {organization_id}")
            
            await manager.broadcast({
                "type": "NEW_NOTIFICATION",
                "organization_id": organization_id
            })
    run_async(_logic())