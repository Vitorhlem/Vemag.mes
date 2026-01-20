from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

# ============================================================================
# 1. TIME SLICES (O CORAÇÃO DO MES)
# ============================================================================
class ProductionTimeSliceBase(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    category: str  # Ex: PRODUCING, PLANNED_STOP, UNPLANNED_STOP, IDLE
    reason: Optional[str] = None
    is_productive: bool = False

class ProductionTimeSliceCreate(ProductionTimeSliceBase):
    vehicle_id: int
    session_id: Optional[int] = None
    order_id: Optional[int] = None

class ProductionTimeSliceRead(ProductionTimeSliceBase):
    id: int
    vehicle_id: int
    
    class Config:
        from_attributes = True

# ============================================================================
# 2. EVENTOS DE PRODUÇÃO (GATILHOS)
# ============================================================================
class ProductionEventCreate(BaseModel):
    machine_id: int
    operator_badge: str
    order_code: Optional[str] = None
    
    event_type: str  # STATUS_CHANGE, COUNT, SHIFT_END, ETC
    new_status: Optional[str] = None  # EM OPERAÇÃO, MANUTENÇÃO, PARADA (Ou EN_US)
    
    reason: Optional[str] = None # Motivo da parada selecionado (Ex: "Quebra Mecânica")
    details: Optional[str] = None
    
    quantity_good: Optional[int] = 0
    quantity_scrap: Optional[int] = 0

# ============================================================================
# 3. ORDENS DE PRODUÇÃO (Modelos Internos)
# ============================================================================
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

# ============================================================================
# 4. LOGS (AUDITORIA BRUTA)
# ============================================================================
class ProductionLogRead(BaseModel):
    id: int
    event_type: str
    timestamp: datetime
    new_status: Optional[str] = None
    reason: Optional[str] = None
    details: Optional[str] = None
    operator_name: Optional[str] = None 

    class Config:
        from_attributes = True

# ============================================================================
# 5. SESSÕES & KPI
# ============================================================================
class SessionStartSchema(BaseModel):
    machine_id: int
    operator_badge: str
    order_code: str

class SessionStopSchema(BaseModel):
    machine_id: int
    operator_badge: str

class SessionDetail(BaseModel):
    id: int
    machine_name: str
    order_code: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: str
    efficiency: float
    
    # NOVO: Inclui a lista de fatias de tempo para desenhar o Gráfico de Gantt
    time_slices: List[ProductionTimeSliceRead] = []

    class Config:
        from_attributes = True

# ============================================================================
# 6. RELATÓRIOS CONSOLIDADOS
# ============================================================================
class StopReasonStat(BaseModel):
    label: str
    count: int
    duration_minutes: float

class EmployeeStatsRead(BaseModel):
    id: int
    employee_name: str
    total_hours: float
    productive_hours: float
    unproductive_hours: float
    efficiency: float
    top_reasons: List[dict]

class EmployeeDetailRead(BaseModel):
    total_hours: float
    productive_hours: float
    unproductive_hours: float
    efficiency: float
    top_reasons: List[StopReasonStat]
    sessions: List[SessionDetail]

# ============================================================================
# 7. ANDON
# ============================================================================
class AndonCreate(BaseModel):
    machine_id: int
    operator_badge: str
    sector: str
    notes: Optional[str] = None

# ============================================================================
# 8. INTEGRAÇÃO SAP (APONTAMENTO)
# ============================================================================
class ProductionAppointmentCreate(BaseModel):
    op_number: str
    service_code: str          # U_Servico
    position: str
    operation: str
    operator_id: str           # Crachá
    resource_code: str         # Recurso (ex: "4.02.01")
    start_time: datetime
    end_time: datetime
    item_code: Optional[str] = "" 
    stop_reason: Optional[str] = ""

# ============================================================================
# 9. LEITURA DE O.P. E ROTEIRO
# ============================================================================

# IMPORTANTE: Definido ANTES de ser usado em ProductionOrderRead
class OperationStepSchema(BaseModel):
    seq: int
    resource: str
    name: str
    description: Optional[str] = ""
    timeEst: float
    status: str = "PENDING"

class ProductionOrderRead(BaseModel):
    op_number: int          # DocNum
    item_code: str          # ItemCode
    part_name: str          # ProdName
    planned_qty: float      # PlannedQty
    uom: str                # InventoryUOM
    type: str = "Standard"  # ProductionOrderType
    custom_ref: str         # U_LGO_DocEntryOPsFather
    
    # Campo novo para o roteiro
    steps: List[OperationStepSchema] = [] 
    
    class Config:
        from_attributes = True # Pydantic v2