#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- CONFIGURAÇÕES DE REDE ---
const char* ssid = "IOT";
const char* password = "007481Ab";
String serverPath = "http://192.168.0.22:8000/api/v1/production/event";

// --- PINOS DE VALIDAÇÃO CRUZADA ---
const int pinMain = 13;      // Contato N.A. (Normalmente Aberto)
const int pinValidator = 14; // Contato N.F. (Normalmente Fechado) - SEGURO PARA BOOT

// --- VARIÁVEIS DE CONTROLE ---
int lastSentState = -1; 
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 500; // 500ms de segurança

// Variáveis apenas para não flodar o painel de logs com mensagens repetidas
int lastLoggedMain = -1;
int lastLoggedVal = -1;

void setup() {
  Serial.begin(115200);
  delay(1000); // Dá um tempo para o monitor serial abrir
  
  Serial.println("\n=========================================");
  Serial.println("🚀 INICIANDO SISTEMA MES - ESP32 🚀");
  Serial.println("=========================================");
  
  Serial.print("🔧 Configurando Pinos... Principal: ");
  Serial.print(pinMain);
  Serial.print(" | Validador: ");
  Serial.println(pinValidator);

  pinMode(pinMain, INPUT_PULLDOWN);
  pinMode(pinValidator, INPUT_PULLDOWN);

  conectarWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ [ALERTA] Conexão WiFi perdida! Interrompendo leituras...");
    conectarWiFi();
  }

  // Leituras brutas
  int stateMain = digitalRead(pinMain);
  int stateVal = digitalRead(pinValidator);
  
  // LOG: Só avisa se os pinos mudarem fisicamente (evita travar o console)
  if (stateMain != lastLoggedMain || stateVal != lastLoggedVal) {
    Serial.print("⚡ [LEITURA FÍSICA] Pino Principal: ");
    Serial.print(stateMain);
    Serial.print(" | Pino Validador: ");
    Serial.println(stateVal);
    
    lastLoggedMain = stateMain;
    lastLoggedVal = stateVal;
  }

  int confirmedState = -1;

  // Lógica de Redundância
  if (stateMain == HIGH && stateVal == LOW) {
    confirmedState = 1; // LIGADA
  } 
  else if (stateMain == LOW && stateVal == HIGH) {
    confirmedState = 0; // DESLIGADA
  } 
  else {
    // Estado inválido detectado (0-0 ou 1-1)
    if (stateMain != lastLoggedMain || stateVal != lastLoggedVal) {
      Serial.println("🚫 [IGNORADO] Estado ambíguo detectado (Ruído ou Transição). Nenhuma ação tomada.");
    }
    return; // Para a execução do loop aqui e recomeça
  }

  // Verifica se o estado confirmado é diferente do que o SAP/MES acha que é
  if (confirmedState != lastSentState) {
    
    // Calcula o tempo do Debounce para ver se o sinal firmou
    if ((millis() - lastDebounceTime) > debounceDelay) {
      Serial.println("⏱️ [DEBOUNCE] Sinal estabilizado. Preparando para envio...");
      
      // Tenta enviar. Se der certo, atualiza a memória do ESP32
      if (enviarSinalParaSistema(confirmedState)) {
        lastSentState = confirmedState;
        Serial.println("✅ [SISTEMA] Estado interno do ESP32 atualizado com sucesso!");
      } else {
        Serial.println("❌ [SISTEMA] Falha ao notificar a API. Tentarei novamente em 500ms.");
      }
      
      lastDebounceTime = millis();
      Serial.println("-----------------------------------------");
    }
  } else {
    // Mantém o timer zerado enquanto não houver mudança real
    lastDebounceTime = millis();
  }
}

// ---------------------------------------------------------
// FUNÇÕES AUXILIARES COM LOGS DETALHADOS
// ---------------------------------------------------------

void conectarWiFi() {
  WiFi.disconnect();
  delay(100);
  WiFi.begin(ssid, password);
  
  Serial.print("📡 [WIFI] Conectando à rede '");
  Serial.print(ssid);
  Serial.print("' ");
  
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n🟢 [WIFI] Conectado com Sucesso!");
    Serial.print("   ↳ IP Recebido: ");
    Serial.println(WiFi.localIP());
    Serial.print("   ↳ Força do Sinal (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n🔴 [WIFI] Falha ao reconectar. O loop tentará novamente.");
  }
}

bool enviarSinalParaSistema(int estado) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ [HTTP] Abortado: Sem conexão WiFi.");
    return false;
  }

  HTTPClient http;
  
  Serial.print("🌐 [HTTP] Iniciando conexão com: ");
  Serial.println(serverPath);
  
  http.begin(serverPath);
  http.addHeader("Content-Type", "application/json");

  // Monta o Payload JSON
  StaticJsonDocument<200> doc;
  doc["machine_id"] = 1;
  doc["event_type"] = "STATUS_CHANGE";
  doc["new_status"] = (estado == 1) ? "1" : "0";
  doc["operator_badge"] = "ESP32_HARDWARE";

  String jsonOutput;
  serializeJson(doc, jsonOutput);

  Serial.print("📦 [HTTP] Payload montado: ");
  Serial.println(jsonOutput);

  // Faz o disparo POST
  unsigned long startTimer = millis();
  int httpResponseCode = http.POST(jsonOutput);
  unsigned long timeTaken = millis() - startTimer;

  // Analisa a resposta
  if (httpResponseCode > 0) {
    Serial.print("📩 [HTTP] Resposta recebida em ");
    Serial.print(timeTaken);
    Serial.print("ms | Código: ");
    Serial.println(httpResponseCode);
    
    // Pega o texto exato que o seu Python respondeu
    String responseBody = http.getString();
    Serial.print("   ↳ Corpo da Resposta: ");
    Serial.println(responseBody);
    
    http.end();
    return true; 
  } else {
    Serial.print("🛑 [HTTP] ERRO FATAL de rede | Código do erro: ");
    Serial.println(httpResponseCode);
    Serial.print("   ↳ Detalhe: ");
    Serial.println(http.errorToString(httpResponseCode).c_str());
    
    http.end();
    return false; 
  }
}