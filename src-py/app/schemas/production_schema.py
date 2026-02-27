from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Union
from datetime import datetime, date

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
    # Deixe o operador opcional também, caso o Arduino esqueça de mandar
    operator_badge: Optional[str] = "ARDUINO_DEFAULT" 
    order_code: Optional[str] = None
    
    event_type: str  # STATUS_CHANGE
    new_status: Optional[str] = None  # RUNNING ou STOPPED
    
    # 🚀 A CORREÇÃO MÁGICA ESTÁ AQUI:
    # Adicionamos '= None' para o Pydantic entender que pode vir vazio.
    timestamp: Optional[datetime] = None 
    
    reason: Optional[str] = None 
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
    operator_id: Optional[int] = None # Link clicável

    class Config:
        from_attributes = True
# ============================================================================
# 5. SESSÕES & KPI
# ============================================================================
class SessionStartSchema(BaseModel):
    op_number: Union[str, int]  # Aceita '3430' ou '03.000...'
    step_seq: str               # Ex: '010'
    machine_id: int             # ID numérico da máquina
    operator_badge: str
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
    # Usar List[Any] ou List[Dict] evita erro 422 se o formato interno variar
    top_reasons: List[Any] = [] 

    class Config:
        from_attributes = True
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
    # Tornando campos opcionais com padrão "" para aceitar o payload de Parada
    op_number: Optional[str] = ""          # U_NumeroDocumento
    service_code: Optional[str] = ""       # U_Servico / U_Servico
    position: Optional[str] = ""           # U_Posicao
    operation: Optional[str] = ""          # U_Operacao
    operation_desc: Optional[str] = ""     # U_DescricaoOperacao
    
    # Campos que você definiu como necessários para Parada
    stop_reason: Optional[str] = ""        # MOTIVO DA PARADA
    resource_code: str                     # RECURSO (Obrigatório em todos)
    operator_id: str                       # OPERADOR (Obrigatório em todos)
    start_time: datetime                   # DATA/HORA INI
    end_time: datetime                     # DATA/HORA FIM
    stop_description: Optional[str] = None # DESCRICAO DA PARADA
    resource_name: Optional[str] = ""      # DESCRICAO DO RECURSO
    operator_name: Optional[str] = ""      # NOME DO OPERADOR
    
    # Campos de contexto O.P. / O.S.
    part_description: Optional[str] = ""   # DESCRICAO ITEM
    item_code: Optional[str] = ""          # CODIGO ITEM
    
    # Controle Interno
    vehicle_id: Optional[int] = None

    class Config:
        from_attributes = True

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
    # ✅ CORREÇÃO: Aceita '4152' (O.P.) e 'OS-4595-1' (O.S.)
    op_number: Union[str, int]  
    
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

class MachineDailyStats(BaseModel):
    date: str
    total_running_operator_seconds: float = 0  # Produzindo com gente
    total_running_autonomous_seconds: float = 0 # Produzindo sozinho (Troca de turno)
    total_paused_operator_seconds: float = 0   # Parado com gente (Almoço, Banheiro, etc)
    total_maintenance_seconds: float = 0       # Quebrado/Manutenção
    total_idle_seconds: float = 0              # Ocioso (Sem turno)
    
    # Campos formatados para exibição (ex: "02:15:00")
    formatted_running_operator: Optional[str] = "00:00:00"
    formatted_running_autonomous: Optional[str] = "00:00:00"
    formatted_paused_operator: Optional[str] = "00:00:00"
    formatted_maintenance: Optional[str] = "00:00:00"


class SessionStart(BaseModel):
    # Aceita '3430' ou '03.000.1' e ignora se vier como string ou int
    op_number: Union[str, int]
    
    # Se o front enviar 'seq' ou 'step_seq', o backend vai aceitar
    step_seq: str               # Ex: '010', '020'
    
    # IDs de sistema
    machine_id: int
    operator_badge: str
    
    # Campos opcionais para não dar erro se o front não enviar
    resource_code: Optional[str] = None
    description: Optional[str] = None

    class Config:
        populate_by_name = True # Permite usar o nome do campo ou o alias

class SessionResponse(BaseModel):
    status: str
    message: str
    session_id: str


class AppointmentCreate(BaseModel):
    op_number: str
    operator_id: str  # Crachá
    vehicle_id: Optional[int] = None
    DataSource: Optional[str] = "I"
    start_time: datetime
    end_time: datetime
    
    position: Optional[str] = None      # Etapa (010, 020...)
    operation: Optional[str] = None     # Código da operação
    operation_desc: Optional[str] = None
    
    item_code: Optional[str] = None
    part_description: Optional[str] = None
    
    stop_reason: Optional[str] = None   # Se for parada
    stop_description: Optional[str] = None
    
    resource_code: Optional[str] = None

class VehicleDailyMetricRead(BaseModel):
    id: int
    date: date
    vehicle_id: int
    organization_id: int
    total_hours: float
    running_hours: float
    idle_hours: float
    maintenance_hours: float
    planned_stop_hours: float
    # ✅ ADICIONE ESTE CAMPO:
    micro_stop_hours: float = 0.0 
    availability: float
    utilization: float
    top_reasons_snapshot: List[Any] = []
    # Placeholders para KPIs
    mtbf: float = 0.0
    mttr: float = 0.0
    closed_at: datetime

    model_config = ConfigDict(from_attributes=True)

# SCHEMA PARA OS CARDS PROFISSIONAIS E GRÁFICO DE PARETO
class MachinePeriodSummary(BaseModel):
    total_running: float
    total_setup: float
    total_pause: float
    total_maintenance: float
    # ✅ ADICIONE ESTE CAMPO:
    total_micro_stops: float = 0.0 
    avg_availability: float
    stop_reasons: List[Any]
    mtbf: float = 0.0
    mttr: float = 0.0

    model_config = ConfigDict(from_attributes=True)