#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// =========================================================
// ⚙️ CONFIGURAÇÕES PRINCIPAIS DO EQUIPAMENTO
// =========================================================
const int MACHINE_ID = 1;  // 🔴 MUDE AQUI PARA O ID DA MÁQUINA (Ex: 2, 3, 4...)
// =========================================================

// --- CONFIGURAÇÕES DE REDE ---
const char* ssid = "IOT";
const char* password = "007481Ab";
String serverPath = "http://192.168.0.22:8000/api/v1/production/event";

// --- PINO DE LEITURA (SIMPLIFICADO) ---
const int pinMain = 13;      // Único pino de leitura para o teste

// --- VARIÁVEIS DE CONTROLE ---
int lastSentState = -1; 
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 500; // 500ms de segurança (debounce)

// Variável apenas para não flodar o painel de logs com mensagens repetidas
int lastLoggedMain = -1;

void setup() {
  Serial.begin(115200);
  delay(1000); // Dá um tempo para o monitor serial abrir
  
  Serial.println("\n=========================================");
  Serial.println("🚀 INICIANDO SISTEMA MES - ESP32 (MODO SIMPLIFICADO) 🚀");
  Serial.print("🏭 MÁQUINA CONFIGURADA: ID ");
  Serial.println(MACHINE_ID);
  Serial.println("=========================================");
  
  Serial.print("🔧 Configurando Pino Principal: ");
  Serial.println(pinMain);

  // Configura o pino com resistor interno puxando pro GND quando estiver solto
  pinMode(pinMain, INPUT_PULLDOWN);

  conectarWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ [ALERTA] Conexão WiFi perdida! Interrompendo leituras...");
    conectarWiFi();
  }

  // Leitura bruta do único pino
  int stateMain = digitalRead(pinMain);
  
  // LOG: Só avisa se o pino mudar fisicamente (evita travar o console)
  if (stateMain != lastLoggedMain) {
    Serial.print("⚡ [LEITURA FÍSICA] Pino Principal (13) mudou para: ");
    Serial.println(stateMain == HIGH ? "HIGH (LIGADO)" : "LOW (DESLIGADO)");
    
    lastLoggedMain = stateMain;
  }

  // A lógica agora é direta: HIGH = 1 (LIGADA), LOW = 0 (DESLIGADA)
  int confirmedState = (stateMain == HIGH) ? 1 : 0;

  // Verifica se o estado confirmado é diferente do que o backend já sabe
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
  
  doc["machine_id"] = MACHINE_ID; 
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