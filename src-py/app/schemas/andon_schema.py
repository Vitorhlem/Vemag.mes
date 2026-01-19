from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.andon_model import AndonStatus, AndonSector

# Base
class AndonCallBase(BaseModel):
    sector: AndonSector
    reason: Optional[str] = None
    description: Optional[str] = None

# Criação (O Kiosk envia isso)
class AndonCallCreate(AndonCallBase):
    machine_id: int

# Update (Técnico assume ou resolve)
class AndonCallUpdate(BaseModel):
    status: Optional[AndonStatus] = None
    description: Optional[str] = None

# Leitura (A TV recebe isso)
class AndonCallResponse(AndonCallBase):
    id: int
    machine_id: int
    machine_name: str  # Campo computado para facilitar o frontend
    machine_sector: Optional[str] = None
    
    status: AndonStatus
    opened_at: datetime
    accepted_at: Optional[datetime] = None
    accepted_by_name: Optional[str] = None # Nome do técnico
    
    class Config:
        from_attributes = True