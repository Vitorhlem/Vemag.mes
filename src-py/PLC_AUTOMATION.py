import requests
import time

# --- CONFIGURAÇÕES ---
# Substitua pelo IP real do seu servidor
API_BASE_URL = "http://192.168.0.22:8000/api/v1"
MACHINE_ID = 1 

# Badge alterado para ficar idêntico ao código do ESP32
PLC_BADGE = "ESP32_HARDWARE" 

def enviar_evento_maquina(novo_status):
    """
    Envia o sinal para o backend exatamente no mesmo formato do ESP32.
    O backend agora cuidará de:
    1. Fechar/Abrir fatias no banco local.
    2. Realizar o apontamento automático no SAP.
    3. Notificar o Tablet via WebSocket.
    """
    endpoint = f"{API_BASE_URL}/production/event"
    
    # Payload ajustado para ser um espelho do jsonOutput do C++
    payload = {
        "machine_id": MACHINE_ID,
        "event_type": "STATUS_CHANGE",
        "new_status": novo_status, # Agora envia "1" ou "0"
        "operator_badge": PLC_BADGE
    }
    
    try:
        print(f"📦 [HTTP] Payload montado: {payload}")
        print(f"📡 [PLC-SIM] Enviando sinal: {novo_status}...")
        
        start_timer = time.time()
        response = requests.post(endpoint, json=payload, timeout=5)
        time_taken = int((time.time() - start_timer) * 1000)
        
        if response.status_code == 200:
            print(f"📩 [HTTP] Resposta recebida em {time_taken}ms | Código: {response.status_code}")
            print(f"   ↳ Corpo da Resposta: {response.text}")
            print("✅ [SISTEMA] Estado interno do ESP32 atualizado com sucesso!\n")
        else:
            print(f"🛑 [HTTP] ERRO FATAL de rede | Código do erro: {response.status_code}")
            print(f"   ↳ Detalhe: {response.text}\n")
            
    except Exception as e:
        print(f"❌ [HTTP] Abortado: Falha crítica de conexão: {e}\n")

# --- INTERFACE DE SIMULAÇÃO ---
print("=========================================")
print("🚀 INICIANDO SISTEMA MES - SIMULADOR PYTHON 🚀")
print(f"🏭 MÁQUINA CONFIGURADA: ID {MACHINE_ID}")
print("=========================================")
print("Comandos:")
print(" [1] - Simular Máquina LIGADA (Produzindo)")
print(" [0] - Simular Máquina DESLIGADA (Parada)")
print(" [Q] - Sair")
print("-----------------------------------------")

while True:
    opcao = input("Aguardando comando: ").strip().upper()
    
    if opcao == '1':
        # Envia status "1" simulando a leitura HIGH/LOW dos pinos do ESP32
        enviar_evento_maquina("1") 
        print("-----------------------------------------")
        
    elif opcao == '0':
        # Envia status "0" simulando a leitura LOW/HIGH dos pinos do ESP32
        enviar_evento_maquina("0") 
        print("-----------------------------------------")
        
    elif opcao == 'Q':
        print("Encerrando simulador...")
        break
    else:
        print("❌ Comando inválido. Use 1, 0 ou Q.")