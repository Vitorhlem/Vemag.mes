# TruCar Backend

This is the backend API for TruCar (VEMAG.mes), built with **FastAPI**.

## 🛠 Tech Stack

-   **Framework**: FastAPI
-   **Database**: PostgreSQL (Async SQLAlchemy)
-   **Migrations**: Alembic
-   **Task Queue**: Celery (with Redis)
-   **Testing**: Pytest

## 🚀 Setup & Installation (Manual)

### 1. Prerequisites

-   Python 3.10+
-   PostgreSQL running
-   Redis running

### 2. Install Dependencies

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and fill in your database credentials, Redis URL, and other secrets.

### 4. Database Migrations

Run Alembic to apply migrations:

```bash
alembic upgrade head
```

### 5. Running the API Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Access API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Running the Celery Worker

For background tasks (emails, notifications), run the worker:

```bash
celery -A app.core.celery_app worker --loglevel=info
```

## 🧪 Running Tests

```bash
pytest
```

## 📂 Structure

-   `app/`: Main application code
    -   `api/`: API endpoints (routers)
    -   `core/`: Configuration, security, logging
    -   `db/`: Database session and base models
    -   `models/`: SQLModel/SQLAlchemy models
    -   `schemas/`: Pydantic schemas (DTOs)
    -   `services/`: Business logic
-   `alembic/`: Migration scripts
-   `tests/`: Unit and integration tests
