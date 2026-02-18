#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h> // Instale esta biblioteca no Gerenciador de Bibliotecas

// --- CONFIGURAÇÕES DE REDE ---
const char* ssid = "IOT";
const char* password = "007481Ab";

// --- CONFIGURAÇÃO DA API ---
// Substitua pelo IP do seu computador (o mesmo que aparece no log do Python)
String serverPath = "http://192.168.0.22:8000/api/v1/production/event";

// --- PINOS ---
const int inputPin = 13; 

// --- VARIÁVEIS DE CONTROLE ---
int lastState = -1;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 150; // Proteção para o contato manual não tremer

void setup() {
  Serial.begin(115200);
  
  // INPUT_PULLDOWN garante que o pino seja 0 (Parado) quando o fio estiver solto
  pinMode(inputPin, INPUT_PULLDOWN);

  // Inicia Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Conectando ao WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi Conectado!");
  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  int currentState = digitalRead(inputPin);

  // Detecta mudança de estado com filtro de ruído (debounce)
  if (currentState != lastState) {
    if ((millis() - lastDebounceTime) > debounceDelay) {
      lastState = currentState;
      lastDebounceTime = millis();

      // Envia para o sistema
      enviarSinalParaSistema(currentState);
    }
  }
}

void enviarSinalParaSistema(int estado) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverPath);
    http.addHeader("Content-Type", "application/json");

    // Monta o JSON exato que o seu Backend Python espera
    StaticJsonDocument<200> doc;
    doc["machine_id"] = 1;
    doc["event_type"] = "STATUS_CHANGE";
    doc["new_status"] = (estado == HIGH) ? "1" : "0";
    doc["operator_badge"] = "ESP32_HARDWARE";

    String jsonOutput;
    serializeJson(doc, jsonOutput);

    Serial.print("📤 Enviando sinal: ");
    Serial.println(jsonOutput);

    int httpResponseCode = http.POST(jsonOutput);

    if (httpResponseCode > 0) {
      Serial.print("✅ Sucesso! Resposta do Servidor: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("❌ Erro no envio: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("📡 WiFi Desconectado!");
  }
}