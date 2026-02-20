import logging
import httpx
import json # 👈 Importe o json
from datetime import datetime # 👈 Importe o datetime
from app.core.celery_app import celery_app
from app.tasks.notification_tasks import dispatch_notification

@celery_app.task(name="processar_novo_chamado", bind=True, max_retries=3)
def processar_novo_chamado(self, call_id: int, machine_name: str, sector: str, organization_id: int, call_data: dict):
    try:
        logging.info(f"🚀 [WORKER] Processando chamado: ID {call_id}")
        
        # 1. Dispara Notificação Push (Mobile)
        dispatch_notification.delay(
            message=f"🚨 Novo chamado Andon: {machine_name} requisitando {sector}",
            notification_type="maintenance_request_new",
            organization_id=organization_id,
            send_to_managers=True,
            related_entity_type="andon",
            related_entity_id=call_id
        )

        # 🚀 2. Avisa o AndonBoard via WebSocket (Tratando as DATAS)
        try:
            # Transformamos o dicionário em JSON tratando as datas como strings
            # O 'default=str' converte qualquer objeto datetime em texto automaticamente
            clean_payload = json.loads(
                json.dumps({
                    "type": "NEW_CALL",
                    "data": call_data
                }, default=str) 
            )

            with httpx.Client() as client:
                # Agora enviamos o payload já "limpo" de objetos complexos
                client.post("http://127.0.0.1:8000/api/v1/production/internal/broadcast", json=clean_payload)
                logging.info(f"📣 [CELERY] Painel Andon avisado com sucesso.")
        except Exception as e:
            logging.error(f"⚠️ Falha ao notificar WebSockets: {e}")

        return f"Chamado {call_id} processado."

    except Exception as exc:
        logging.error(f"❌ Erro ao processar chamado {call_id}: {exc}")
        raise self.retry(exc=exc, countdown=10)