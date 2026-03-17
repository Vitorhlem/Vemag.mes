#include <SPI.h>
#include <Ethernet.h>
#include <ArduinoJson.h>

// =========================================================
// ⚙️ CONFIGURAÇÕES
// =========================================================
const int MACHINE_ID = 1;

// --- REDE ---
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress server(192, 168, 0, 5); // IP do seu servidor Linux
int serverPort = 8000;
String endpoint = "/api/v1/production/event";

EthernetClient client;

// --- PINOS (O Loop de Sinal) ---
const int pinSensor = 2;  // PINO DE ENTRADA (Lê o sinal) - D2
const int pinSource = 3;  // PINO DE SAÍDA (Simula o GND) - D3

// --- CONTROLE ---
int lastSentState = -1; 
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 2000; // 2 segundos para ignorar ruído de centelha

void setup() {
  delay(3000); // Espera estabilizar a fonte 9V

  Serial.begin(115200);
  Serial.println("\n🚀 SISTEMA MES - INICIANDO ARDUINO");

  // Configuração dos pinos: D2 lê o que o D3 envia
  pinMode(pinSource, OUTPUT);
  digitalWrite(pinSource, LOW); // D3 sempre em LOW (Terra virtual)

  pinMode(pinSensor, INPUT_PULLUP); // D2 em HIGH interno

  conectarRede();
}

void loop() {
  // Verifica se o cabo de rede está conectado fisicamente
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("⚠️ Cabo de rede desconectado!");
    delay(2000);
    return;
  }

  // --- LEITURA DO RELÉ ---
  int leituraSensor = digitalRead(pinSensor);
  
  // Se leitura for 0 (encostou no D3), estado = 1 (Ligada)
  // Se leitura for 1 (fios soltos), estado = 0 (Parada)
  int estadoAtual = (leituraSensor == LOW) ? 1 : 0;

  // Só envia se o estado mudou
  if (estadoAtual != lastSentState) {
    unsigned long currentMillis = millis();
    if ((currentMillis - lastDebounceTime) > debounceDelay) {
      
      Serial.print("⚡ Mudança detectada: ");
      Serial.println(estadoAtual == 1 ? "MAQUINA PRODUZINDO" : "MAQUINA PARADA");
      
      if (enviarSinalParaSistema(estadoAtual)) {
        lastSentState = estadoAtual;
        lastDebounceTime = currentMillis;
      }
    }
  }
}

void conectarRede() {
  Serial.println("🔌 Buscando IP via DHCP...");
  if (Ethernet.begin(mac) == 0) {
    Serial.println("🔴 Falha ao obter IP. Verifique cabo/DHCP.");
    // Tenta novamente em 5 segundos
    delay(5000);
    return;
  }
  Serial.print("🟢 Conectado! IP: ");
  Serial.println(Ethernet.localIP());
}

bool enviarSinalParaSistema(int estado) {
  if (!client.connect(server, serverPort)) {
    Serial.println("❌ Falha ao conectar no servidor (Porta 8000)");
    return false;
  }

  // Monta JSON idêntico ao que o seu simulador Python usava
  StaticJsonDocument<128> doc;
  doc["machine_id"] = MACHINE_ID;
  doc["event_type"] = "STATUS_CHANGE";
  doc["new_status"] = (estado == 1) ? "1" : "0"; // Envia "1" ou "0"
  doc["operator_badge"] = "ESP32_HARDWARE"; // Badge padrão do sistema

  // Envia cabeçalhos HTTP
  client.print("POST ");
  client.print(endpoint);
  client.println(" HTTP/1.1");
  client.print("Host: ");
  client.println(server);
  client.println("Content-Type: application/json");
  client.print("Content-Length: ");
  client.println(measureJson(doc));
  client.println("Connection: close");
  client.println();
  
  // Envia o corpo do JSON
  serializeJson(doc, client);

  // Lê a resposta básica
  unsigned long timeout = millis();
  while (client.available() == 0) {
    if (millis() - timeout > 2000) {
      Serial.println("⚠️ Timeout na resposta");
      client.stop();
      return false;
    }
  }

  Serial.println("✅ Sincronizado com Sucesso!");
  client.stop();
  return true;
}