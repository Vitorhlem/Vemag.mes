#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// =========================================================
// ⚙️ CONFIGURAÇÕES
// =========================================================
const int MACHINE_ID = 1;

// --- REDE WI-FI ---
const char* ssid = "IOT";
const char* password = "007481Ab";

// URL completa do seu servidor Linux
const char* serverUrl = "http://192.168.0.5:8000/api/v1/production/event";

// --- A SUA LÓGICA SIMPLES (PINOS ESP32) ---
const int pinSensor = 4;  // Pino que vai LER o fio (GPIO 4)
const int pinSource = 5;  // Pino que vai FORNECER o GND (GPIO 5)

int lastSentState = -1; 
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 500; 

int ultimoEstadoFisico = -1; 

void setup() {
  Serial.begin(115200);
  delay(1000); // Tempinho pro monitor serial abrir

  Serial.println("\n🚀 INICIANDO ESP32 - LÓGICA SIMPLES PINOS 4 E 5");

  // Transforma o Pino 5 em um "GND" controlado por software
  pinMode(pinSource, OUTPUT);
  digitalWrite(pinSource, LOW); 

  // Configura o Pino 4 para ler o sinal (nasce como 1)
  pinMode(pinSensor, INPUT_PULLUP);

  conectarWiFi();
}

void loop() {
  // Reconexão automática se o Wi-Fi cair
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ Wi-Fi desconectado! Tentando reconectar...");
    conectarWiFi();
  }

  // --- LEITURA DIRETA ---
  int leitura = digitalRead(pinSensor);
  
  // A Lógica: Encostado = 1, Desencostado = 0
  int sinal = (leitura == LOW) ? 1 : 0;

  // 👀 DEBUG: Mostra na hora se você encostou ou soltou
  if (sinal != ultimoEstadoFisico) {
    Serial.print("👀 [DEBUG] Status Físico: ");
    Serial.println(sinal == 1 ? "ENCOSTADO (Sinal 1)" : "DESENCOSTADO (Sinal 0)");
    ultimoEstadoFisico = sinal;
  }

  // Envia para o servidor depois de meio segundo estabilizado
  if (sinal != lastSentState) {
    if ((millis() - lastDebounceTime) > debounceDelay) {
      
      Serial.print("⚡ Enviando para API: ");
      Serial.println(sinal == 1 ? "RUNNING (1)" : "STOPPED (0)");
      
      if (enviarSinalParaSistema(sinal)) {
        lastSentState = sinal;
      }
      
      lastDebounceTime = millis();
    }
  } else {
    lastDebounceTime = millis();
  }
}

// ---------------------------------------------------------
// FUNÇÕES AUXILIARES DE REDE (ESP32)
// ---------------------------------------------------------

void conectarWiFi() {
  Serial.print("🔌 Conectando ao Wi-Fi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\n🟢 Wi-Fi Conectado!");
  Serial.print("   ↳ IP: ");
  Serial.println(WiFi.localIP());
}

bool enviarSinalParaSistema(int sinal) {
  // O ESP32 tem uma biblioteca HTTP muito mais inteligente
  HTTPClient http;
  
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  // Monta o JSON
  StaticJsonDocument<128> doc;
  doc["machine_id"] = MACHINE_ID;
  doc["event_type"] = "STATUS_CHANGE";
  doc["new_status"] = (sinal == 1) ? "RUNNING" : "STOPPED";
  doc["operator_badge"] = "ESP32_WIFI";

  String jsonOutput;
  serializeJson(doc, jsonOutput);

  // Faz o POST direto passando a String
  int httpResponseCode = http.POST(jsonOutput);
  
  bool ok = false;
  if (httpResponseCode > 0) {
    Serial.print("✅ Enviado pro Linux! Resposta HTTP: ");
    Serial.println(httpResponseCode);
    ok = true;
  } else {
    Serial.print("❌ Erro de Envio: ");
    Serial.println(http.errorToString(httpResponseCode).c_str());
  }
  
  // Fecha a conexão para liberar memória
  http.end();
  
  return ok;
}