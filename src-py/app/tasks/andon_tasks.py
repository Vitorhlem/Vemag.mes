# Localização: app/tasks/andon_tasks.py

from app.core.celery_app import celery_app
import logging
from app.tasks.notification_tasks import dispatch_notification # Importe a tarefa de notificação

@celery_app.task(name="processar_novo_chamado", bind=True, max_retries=3)
def processar_novo_chamado(self, call_id: int, machine_name: str, sector: str, organization_id: int):
    """
    Tarefa disparada via Celery quando um novo Andon é aberto.
    """
    try:
        logging.info(f"🚀 [WORKER] Novo chamado detectado: ID {call_id}")
        
        dispatch_notification.delay(
        message=f"🚨 Novo chamado Andon: {machine_name} requisitando {sector}",
        notification_type="maintenance_request_new", # Tipo definido no seu model
        organization_id=organization_id,
        send_to_managers=True, # Notifica todos os gestores
        related_entity_type="andon",
        related_entity_id=call_id
    )

        print(f"ALERTA FÁBRICA: {sector} requisitado na {machine_name} (Protocolo: {call_id})")

        
        
        return f"Notificação para o chamado {call_id} enviada."
    
    
        
    except Exception as exc:
        # Se falhar (ex: erro de rede no envio da notificação), tenta de novo em 10 segundos
        logging.error(f"❌ Erro ao processar chamado {call_id}: {exc}")
        raise self.retry(exc=exc, countdown=10)