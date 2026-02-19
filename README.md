# TruCar / VEMAG.mes

**TruCar** (also known as VEMAG.mes) is a comprehensive Vehicle Management and Production Monitoring System (MES). It integrates a modern web interface with IoT hardware for real-time tracking and management.

## 🚀 Overview

The system is designed to manage:
- **Vehicles & Fleets**: Tracking maintenance, fuel logs, costs, and tires.
- **Production Monitoring**: Real-time status updates from machinery via IoT devices.
- **Inventory**: Parts and implements management.
- **Logistics**: Freight orders and journey planning.

## 🏗 Architecture

The project is composed of several microservices and components:

1.  **Frontend (`src-client`)**: A Progressive Web App (PWA) built with [Quasar Framework](https://quasar.dev/) (Vue.js 3).
2.  **Backend (`src-py`)**: A RESTful API built with [FastAPI](https://fastapi.tiangolo.com/), handling business logic, database interactions, and WebSocket connections.
3.  **Database**: [PostgreSQL](https://www.postgresql.org/) for persistent data storage.
4.  **Cache & Message Broker**: [Redis](https://redis.io/) for caching and Celery task queue.
5.  **Worker**: [Celery](https://docs.celeryq.dev/) for background tasks (e.g., email notifications, scheduled jobs).
6.  **IoT Hardware (`sketch_feb17a`)**: ESP32-based hardware for machine status monitoring.
7.  **Reverse Proxy**: Nginx (serving the frontend).

## 🛠 Prerequisites

-   [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) (Recommended)
-   **For Manual Development**:
    -   Node.js (v18+) & Yarn/NPM
    -   Python (v3.10+)
    -   PostgreSQL
    -   Redis
    -   Arduino IDE (for IoT)

## 📦 Quick Start (Docker)

The easiest way to run the entire stack is using Docker Compose.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Start the services:**
    ```bash
    docker-compose up --build
    ```

3.  **Access the application:**
    -   **Frontend**: [http://localhost:9000](http://localhost:9000)
    -   **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
    -   **Database**: Port `5432`
    -   **Redis**: Port `6379`

## 📂 Project Structure

```
.
├── docker-compose.yml   # Docker services configuration
├── src-client/          # Frontend source code (Quasar/Vue.js)
├── src-py/              # Backend source code (FastAPI)
├── sketch_feb17a/       # Arduino/ESP32 firmware code
├── project_scanner.py   # Utility script for code analysis
└── ...
```

## 🔧 Manual Setup & Development

### Backend (`src-py`)

Navigate to `src-py/` and follow the instructions in [src-py/README.md](src-py/README.md).

### Frontend (`src-client`)

Navigate to `src-client/` and follow the instructions in [src-client/README.md](src-client/README.md).

### IoT Hardware (`sketch_feb17a`)

Navigate to `sketch_feb17a/` and follow the instructions in [sketch_feb17a/README.md](sketch_feb17a/README.md).

## 🤝 Contributing

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## 📄 License

[MIT](LICENSE)
