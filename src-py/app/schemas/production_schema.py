from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
# --- ANDON ---
class AndonCreate(BaseModel):
    machine_id: int
    operator_badge: str
    sector: str
    notes: Optional[str] = None

# --- EVENTOS ---
class ProductionEventCreate(BaseModel):
    machine_id: int
    operator_badge: str
    order_code: Optional[str] = None
    
    event_type: str 
    new_status: Optional[str] = None 
    reason: Optional[str] = None # Motivo da parada selecionado
    details: Optional[str] = None
    
    quantity_good: Optional[int] = 0
    quantity_scrap: Optional[int] = 0

# --- O.P. ---
class ProductionOrder(BaseModel):
    id: int
    code: str
    part_name: str
    target_quantity: int
    produced_quantity: int
    scrap_quantity: int
    status: str
    part_image_url: Optional[str] = None
    class Config:
        from_attributes = True

class ProductionLogRead(BaseModel):
    id: int
    event_type: str
    timestamp: datetime
    new_status: Optional[str] = None
    reason: Optional[str] = None
    details: Optional[str] = None
    operator_name: Optional[str] = None # Vamos injetar isso manualmente ou via ORM

    class Config:
        from_attributes = True

# --- SCHEMAS DE SESSÃO ---
class SessionStartSchema(BaseModel):
    machine_id: int
    operator_badge: str
    order_code: str

class SessionStopSchema(BaseModel):
    machine_id: int
    operator_badge: str

class EmployeeStatsRead(BaseModel):
    id: int
    employee_name: str
    total_hours: float
    productive_hours: float
    unproductive_hours: float
    efficiency: float
    top_reasons: List[dict]

class StopReasonStat(BaseModel):
    label: str
    count: int
    duration_minutes: float

class SessionDetail(BaseModel):
    id: int
    machine_name: str
    order_code: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: str
    efficiency: float

class EmployeeDetailRead(BaseModel):
    # KPIs Totais do Período
    total_hours: float
    productive_hours: float
    unproductive_hours: float
    efficiency: float
    
    # Listas Reais
    top_reasons: List[StopReasonStat]
    sessions: List[SessionDetail]