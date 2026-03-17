import requests
import time

# --- CONFIGURAÇÕES ---
API_BASE_URL = "http://192.168.0.5:8000/api/v1"
MACHINE_ID = 1 
PLC_BADGE = "ESP32_HARDWARE" 

# Se a sua rota exigir login, coloque o token de acesso (JWT) aqui. 
# Se for uma rota aberta para IoT, deixe em branco.
API_TOKEN = "" 

def enviar_evento_maquina(novo_status):
    # Dica: No FastAPI, se a rota for declarada com barra no final (ex: /event/), 
    # chamar sem a barra causa um erro de redirecionamento (307). 
    endpoint = f"{API_BASE_URL}/production/event"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Injeta o Token de Autorização se ele existir
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    
    # Payload ajustado
    payload = {
        "machine_id": int(MACHINE_ID),     # FastAPI geralmente exige int para IDs
        "event_type": "STATUS_CHANGE",
        "new_status": str(novo_status),    # Mantido como string ("1" ou "0")
        "operator_badge": str(PLC_BADGE)
    }
    
    try:
        print(f"📦 [HTTP] Payload montado: {payload}")
        print(f"📡 [PLC-SIM] Enviando sinal: {novo_status} a partir da Máquina {MACHINE_ID}...")
        
        start_timer = time.time()
        # Passando os headers explicitamente
        response = requests.post(endpoint, json=payload, headers=headers, timeout=5)
        time_taken = int((time.time() - start_timer) * 1000)
        
        # Tratamento detalhado de respostas do FastAPI
        if response.status_code in [200, 201]:
            print(f"📩 [HTTP] Sucesso em {time_taken}ms | Código: {response.status_code}")
            print("✅ [SISTEMA] Estado interno atualizado com sucesso!\n")
            
        elif response.status_code == 422:
            print(f"🛑 [HTTP] Erro 422: O FastAPI rejeitou o formato dos dados!")
            print(f"   ↳ Detalhe do que o backend exigiu: {response.text}\n")
            
        elif response.status_code == 401:
            print(f"🛑 [HTTP] Erro 401: Não Autorizado!")
            print(f"   ↳ A rota exige um Token. Preencha a variável API_TOKEN no topo do script.\n")
            
        else:
            print(f"🛑 [HTTP] Erro {response.status_code} | Falha na comunicação")
            print(f"   ↳ Detalhe: {response.text}\n")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ [HTTP] Abortado: Servidor recusou a conexão. O backend está rodando no IP {API_BASE_URL}?\n")
    except Exception as e:
        print(f"❌ [HTTP] Erro crítico inesperado: {e}\n")

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
        enviar_evento_maquina("1") 
        print("-----------------------------------------")
        
    elif opcao == '0':
        enviar_evento_maquina("0") 
        print("-----------------------------------------")
        
    elif opcao == 'Q':
        print("Encerrando simulador...")
        break
    else:
        print("❌ Comando inválido. Use 1, 0 ou Q.")