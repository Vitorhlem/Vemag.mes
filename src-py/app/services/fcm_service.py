import firebase_admin
from firebase_admin import credentials, messaging
import os

# Inicializa o Firebase apenas uma vez
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # O arquivo deve estar na raiz do container (copiado pelo Dockerfile)
            path = "serviceAccountKey.json"
            if os.path.exists(path):
                cred = credentials.Certificate(path)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase inicializado com sucesso!")
            else:
                print("⚠️ Arquivo serviceAccountKey.json não encontrado. Notificações desativadas.")
        except Exception as e:
            print(f"❌ Erro ao inicializar Firebase: {e}")

# Função para enviar notificação
def send_push_notification(token: str, title: str, body: str, data: dict = None):
    # Garante que está inicializado
    initialize_firebase()
    
    if not token:
        return False

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data if data else {},
            token=token,
        )
        response = messaging.send(message)
        print(f"📨 Notificação enviada: {response}")
        return True
    except Exception as e:
        print(f"❌ Falha no envio: {e}")
        return False