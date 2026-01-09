import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Set, List, Dict, Any, Union
from pydantic import model_validator, Field, AnyHttpUrl, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8', 
        extra="ignore", 
        case_sensitive=True
    )

    PROJECT_NAME: str = "TruCar"
    API_V1_STR: str = "/api/v1"
    FRONTEND_URL: str = "http://localhost:9000"

    # --- CORS ---
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        # Caso 1: String separada por vírgula
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        
        # Caso 2: Lista (se já vier processada ou do JSON)
        elif isinstance(v, (list, tuple)):
            # Filtra strings vazias dentro da lista para evitar o erro de validação
            return [i for i in v if isinstance(i, str) and i.strip()]
            
        return v

    # --- SUPERUSERS ---
    SUPERUSER_EMAILS: Set[str] = set()

    @field_validator("SUPERUSER_EMAILS", mode="before")
    @classmethod
    def assemble_superuser_emails(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {i.strip() for i in v.split(",") if i.strip()}
        return v
    
    # --- INTEGRAÇÕES ---
    OPENWEATHER_API_KEY: Optional[str] = None
    REDIS_URL: Optional[str] = None

    # --- BANCO DE DADOS ---
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    database_url_from_env: Optional[str] = Field(None, alias="DATABASE_URL")
    
    # CORREÇÃO AQUI: Renomeado de SQLALCHEMY_DATABASE_URI para DATABASE_URI
    # para bater com o que o session.py espera.
    DATABASE_URI: Optional[str] = None
    
    @model_validator(mode='after')
    def assemble_db_uri(self) -> 'Settings':
        uri = None
        
        if self.database_url_from_env:
            uri = self.database_url_from_env
            # Ajuste para asyncpg no Render
            if uri.startswith("postgres://"):
                uri = uri.replace("postgres://", "postgresql+asyncpg://", 1)
            elif uri.startswith("postgresql://") and not uri.startswith("postgresql+asyncpg://"):
                uri = uri.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        elif self.POSTGRES_USER and self.POSTGRES_SERVER and self.POSTGRES_DB:
             uri = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
             )
        
        if not uri:
             # Fallback para SQLite local
             uri = "sqlite+aiosqlite:///./test.db" 

        # Atribui ao nome correto
        self.DATABASE_URI = uri
        return self

    # --- SEGURANÇA ---
    SECRET_KEY: str = "CHANGE_ME"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    REFRESH_TOKEN_SECRET_KEY: str = "CHANGE_ME_REFRESH"
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    ALGORITHM: str = "HS256"
    FERNET_KEY: str = "CHANGE_ME_FERNET"

    # --- SMTP ---
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # --- LIMITES DEMO ---
    DEMO_TOTAL_LIMITS: Dict[str, int] = {
        "vehicles": 3,
        "users": 2,
        "parts": 15,
        "clients": 5,
        "implements": 2,
        "vehicle_components": 10,
    }
    
    @field_validator("DEMO_TOTAL_LIMITS", mode="before")
    @classmethod
    def parse_demo_total_limits(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v

    DEMO_MONTHLY_LIMITS: Dict[str, int] = {
        "reports": 5,
        "fines": 3,
        "documents": 10,
        "freight_orders": 10,
        "maintenance_requests": 5,
        "fuel_logs": 20,
        "costs": 15
    }

    @field_validator("DEMO_MONTHLY_LIMITS", mode="before")
    @classmethod
    def parse_demo_monthly_limits(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v

settings = Settings()