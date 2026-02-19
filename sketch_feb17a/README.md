# TruCar / VEMAG.mes IoT Hardware

This folder contains the Arduino sketch for the ESP32-based hardware component used for real-time machine monitoring.

## 🛠 Hardware Requirements

-   **Microcontroller**: ESP32 (or similar Arduino-compatible board with WiFi)
-   **Power Supply**: 5V USB or similar
-   **Machine Interface**: Simple digital input (switch/relay/optocoupler)
-   **Wiring**:
    -   **Signal Input**: Pin 13
    -   **Ground**: GND

## 🚀 Setup & Installation

### 1. Prerequisites

-   [Arduino IDE](https://www.arduino.cc/en/software)
-   **Board Manager**: Install "ESP32 by Espressif Systems"
-   **Library Manager**: Install `ArduinoJson` (by Benoit Blanchon)

### 2. Configuration

Open `sketch_feb17a.ino` in Arduino IDE and update the following lines:

1.  **WiFi Credentials**:
    ```cpp
    const char* ssid = "YOUR_WIFI_SSID";
    const char* password = "YOUR_WIFI_PASSWORD";
    ```

2.  **API Endpoint**:
    Update the `serverPath` to point to your backend server's IP address:
    ```cpp
    String serverPath = "http://YOUR_SERVER_IP:8000/api/v1/production/event";
    ```
    *Note: If running the backend locally, use your computer's IP address (e.g., `192.168.0.22`), not `localhost`.*

3.  **Machine ID**:
    Currently hardcoded as `1`. You can modify this in the code if needed:
    ```cpp
    doc["machine_id"] = 1;
    ```

### 3. Uploading

1.  Connect your ESP32 via USB.
2.  Select the correct board and port in Arduino IDE.
3.  Click **Upload** (Arrow icon).
4.  Open the **Serial Monitor** (115200 baud) to view logs.

## 📡 Operation

The device monitors the input pin (Pin 13). When the state changes (High/Low) and persists for the debounce period (150ms), it sends a JSON payload to the backend:

```json
{
  "machine_id": 1,
  "event_type": "STATUS_CHANGE",
  "new_status": "1", // or "0"
  "operator_badge": "ESP32_HARDWARE"
}
```

The LED on the board (if available on Pin 2) or Serial Monitor will indicate successful transmission.
