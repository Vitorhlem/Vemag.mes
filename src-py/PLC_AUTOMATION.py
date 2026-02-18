import requests
import time
from datetime import datetime

# --- CONFIGURAÇÕES ---
# Substitua pelo IP real do seu servidor
API_BASE_URL = "http://192.168.0.22:8000/api/v1"
MACHINE_ID = 1 
# Badge especial para identificar que o comando veio da automação
PLC_BADGE = "PLC_AUTOMATION" 

def enviar_evento_maquina(novo_status):
    """
    Envia o sinal para o backend. 
    O backend agora cuidará de:
    1. Fechar/Abrir fatias no banco local.
    2. Realizar o apontamento automático no SAP.
    3. Notificar o Tablet via WebSocket.
    """
    endpoint = f"{API_BASE_URL}/production/event"
    
    payload = {
        "machine_id": MACHINE_ID,
        "event_type": "STATUS_CHANGE",
        "new_status": novo_status,
        "operator_badge": PLC_BADGE,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        print(f"📡 [PLC-SIM] Enviando sinal: {novo_status}...")
        response = requests.post(endpoint, json=payload, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Sucesso! Resposta do Servidor: {response.json()}")
        else:
            print(f"⚠️ Erro no servidor ({response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"❌ Falha crítica de conexão: {e}")

# --- INTERFACE DE SIMULAÇÃO ---
print("==========================================")
print("   SIMULADOR PLC - VEMAG MES AUTOMATION   ")
print("==========================================")
print("Comandos:")
print(" [1] - Simular Máquina LIGADA (Produzindo)")
print(" [0] - Simular Máquina DESLIGADA (Parada)")
print(" [Q] - Sair")
print("------------------------------------------")

while True:
    opcao = input("Aguardando comando: ").strip().upper()
    
    if opcao == '1':
        # Envia status que o backend mapeia para PRODUCING
        enviar_evento_maquina("RUNNING") 
        print("🚀 Sinal de MÁQUINA LIGADA enviado.")
        
    elif opcao == '0':
        # Envia status que o backend mapeia para UNPLANNED_STOP
        # Isso disparará o apontamento SAP e abrirá o diálogo no Cockpit
        enviar_evento_maquina("IDLE") 
        print("🛑 Sinal de MÁQUINA PARADA enviado.")
        
    elif opcao == 'Q':
        print("Encerrando simulador...")
        break
    else:
        print("❌ Comando inválido. Use 1, 0 ou Q.")