import firebase_admin
from firebase_admin import credentials, messaging
import os
import logging

# Configuração de Logs para aparecer no Docker
logger = logging.getLogger(__name__)

# --- SUA LÓGICA ORIGINAL (Mantida e melhorada com Logging) ---

def initialize_firebase():
    """
    Inicializa o app do Firebase verificando o arquivo de credenciais.
    """
    if not firebase_admin._apps:
        try:
            # Tenta o nome que você definiu: serviceAccountKey.json
            path = "serviceAccountKey.json"
            
            # Fallback: Se não achar, tenta o nome padrão que sugeri antes (firebase_credentials.json)
            # para garantir que funcione independente de como você salvou o arquivo.
            if not os.path.exists(path):
                if os.path.exists("firebase_credentials.json"):
                    path = "firebase_credentials.json"

            if os.path.exists(path):
                cred = credentials.Certificate(path)
                firebase_admin.initialize_app(cred)
                logger.info(f"✅ Firebase inicializado com sucesso! (Via: {path})")
            else:
                logger.warning("⚠️ Arquivo de credenciais (serviceAccountKey.json) não encontrado. Notificações não funcionarão.")
        except Exception as e:
            logger.error(f"❌ Erro crítico ao inicializar Firebase: {e}")

def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """
    Envia notificação para um único dispositivo (usado no teste manual).
    """
    # Garante que está inicializado
    initialize_firebase()
    
    if not token:
        return False

    try:
        # CORREÇÃO IMPORTANTE: Firebase exige que valores de 'data' sejam strings
        safe_data = {k: str(v) for k, v in (data or {}).items()}

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=safe_data,
            token=token,
        )
        response = messaging.send(message)
        logger.info(f"📨 Notificação individual enviada. ID: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ Falha no envio individual: {e}")
        return False

# --- NOVA FUNÇÃO (Para Automação de Grupos/Setores) ---

def enviar_push_lista(tokens: list, title: str, body: str, data: dict = None):
    initialize_firebase()

    if not tokens:
        return 0

    # Limpeza de tokens
    tokens_limpos = list(set([t for t in tokens if t]))
    
    if not tokens_limpos:
        return 0

    # Conversão de dados para string (obrigatório do Firebase)
    safe_data = {k: str(v) for k, v in (data or {}).items()}
    
    sucessos = 0

    # --- CORREÇÃO: Envio Individual (Loop) para evitar erro 404 do Batch ---
    for token in tokens_limpos:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=safe_data,
                token=token, # Envia para um token específico
            )
            
            # Usa o método .send() que usa a API V1 HTTP (mais moderna e estável)
            messaging.send(message)
            sucessos += 1
            
        except Exception as e:
            # Se um token falhar (ex: app desinstalado), apenas loga e continua
            logger.warning(f"⚠️ Falha ao enviar para um dispositivo específico: {e}")
            continue

    logger.info(f"📢 Broadcast finalizado: {sucessos}/{len(tokens_limpos)} enviados com sucesso.")
    return sucessos