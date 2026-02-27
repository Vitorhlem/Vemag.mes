#include <SPI.h>
#include <Ethernet.h>
#include <ArduinoJson.h>

// =========================================================
// ⚙️ CONFIGURAÇÕES
// =========================================================
const int MACHINE_ID = 1;

// --- REDE ---
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress server(192, 168, 0, 22);
int serverPort = 8000;
String endpoint = "/api/v1/production/event";

EthernetClient client;

// --- PINOS (O Loop de Sinal) ---
const int pinSource = 3;  // PINO DE SAÍDA (Vai agir como Terra/GND)
const int pinSensor = 2;  // PINO DE ENTRADA (Vai ler o sinal)

// --- CONTROLE ---
int lastSentState = -1; 
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 2000; // Aumentei para 2s para evitar falsos positivos do disjuntor batendo

void setup() {
  // 1. SOLUÇÃO DA FONTE 9V: Espera a energia estabilizar antes de ligar o Shield
  delay(5000); 

  Serial.begin(115200);
  while (!Serial) { ; } 

  Serial.println("\n🚀 INICIANDO SISTEMA MES - LOOP 2 PINOS");

  // 2. CONFIGURAÇÃO DOS PINOS (A Mágica do Loop)
  
  // Configura o Pino 3 como SAÍDA e força ele a ser NEGATIVO (LOW)
  // Ele vai agir como se fosse um pino GND, mas controlado por software.
  pinMode(pinSource, OUTPUT);
  digitalWrite(pinSource, LOW); 

  // Configura o Pino 2 como ENTRADA com resistor interno ativado
  pinMode(pinSensor, INPUT_PULLUP);

  conectarRede();
}

void loop() {
  // Reconexão automática se o cabo cair
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("⚠️ Cabo de rede desconectado!");
    delay(2000);
    return;
  }

  // --- LEITURA DO LOOP ---
  // Se o relé FECHAR, o Pino 2 encosta no Pino 3 (LOW). Leitura = 0.
  // Se o relé ABRIR, o Pino 2 fica solto (PullUp). Leitura = 1.
  int leituraSensor = digitalRead(pinSensor);
  
  // Converte a leitura elétrica para Lógica de Negócio
  // Leitura 0 (LOW) significa que o circuito fechou -> MÁQUINA LIGADA
  int estadoAtual = (leituraSensor == LOW) ? 1 : 0;

  // Lógica de envio (Só envia se mudar)
  if (estadoAtual != lastSentState) {
    if ((millis() - lastDebounceTime) > debounceDelay) {
      
      Serial.print("⚡ Estado Mudou para: ");
      Serial.println(estadoAtual == 1 ? "LIGADA (RUNNING)" : "DESLIGADA (STOPPED)");
      
      if (enviarSinalParaSistema(estadoAtual)) {
        lastSentState = estadoAtual;
      }
      
      lastDebounceTime = millis();
    }
  } else {
    lastDebounceTime = millis();
  }
}

// ---------------------------------------------------------
// FUNÇÕES AUXILIARES
// ---------------------------------------------------------

void conectarRede() {
  Serial.println("🔌 Conectando Ethernet (DHCP)...");
  if (Ethernet.begin(mac) == 0) {
    Serial.println("🔴 Falha DHCP. Verifique cabo/roteador.");
    while (true) delay(1000); // Trava se não tiver rede
  }
  delay(1000);
  Serial.print("🟢 IP: ");
  Serial.println(Ethernet.localIP());
}

bool enviarSinalParaSistema(int estado) {
  if (!client.connected()) {
    client.stop();
    if (!client.connect(server, serverPort)) return false;
  }

  // Monta JSON Otimizado
  StaticJsonDocument<128> doc;
  doc["machine_id"] = MACHINE_ID;
  doc["event_type"] = "STATUS_CHANGE";
  // Envia as strings exatas que o Python espera
  doc["new_status"] = (estado == 1) ? "RUNNING" : "STOPPED";
  doc["operator_badge"] = "ARDUINO_LOOP";

  size_t len = measureJson(doc);

  // Envia HTTP
  client.print("POST ");
  client.print(endpoint);
  client.println(" HTTP/1.1");
  client.print("Host: ");
  client.println(server);
  client.println("Connection: close");
  client.println("Content-Type: application/json");
  client.print("Content-Length: ");
  client.println(len);
  client.println();
  
  serializeJson(doc, client); // Envia corpo direto para a rede

  // Aguarda resposta rápida
  unsigned long t = millis();
  bool ok = false;
  while (client.connected() && millis() - t < 2000) {
    if (client.available()) { client.read(); ok = true; t = millis(); }
  }
  client.stop();
  
  if(ok) Serial.println("✅ Enviado!");
  else Serial.println("❌ Erro de Envio");
  
  return ok;
}