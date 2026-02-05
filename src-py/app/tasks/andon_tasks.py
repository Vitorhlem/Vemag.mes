# Localização: app/tasks/andon_tasks.py

from app.core.celery_app import celery_app
import logging

@celery_app.task(name="processar_novo_chamado", bind=True, max_retries=3)
def processar_novo_chamado(self, call_id: int, machine_name: str, sector: str):
    """
    Tarefa disparada via Celery quando um novo Andon é aberto.
    """
    try:
        logging.info(f"🚀 [WORKER] Novo chamado detectado: ID {call_id}")
        
        # Aqui você pode colocar lógicas pesadas, por exemplo:
        # 1. Enviar Notificação Push para os técnicos do setor
        # 2. Enviar mensagem em canal de Slack/Telegram
        # 3. Registrar log de auditoria externa
        
        # Exemplo de log de saída
        print(f"ALERTA FÁBRICA: {sector} requisitado na {machine_name} (Protocolo: {call_id})")
        
        return f"Notificação para o chamado {call_id} enviada."
        
    except Exception as exc:
        # Se falhar (ex: erro de rede no envio da notificação), tenta de novo em 10 segundos
        logging.error(f"❌ Erro ao processar chamado {call_id}: {exc}")
        raise self.retry(exc=exc, countdown=10)