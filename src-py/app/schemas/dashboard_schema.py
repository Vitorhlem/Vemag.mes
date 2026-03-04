from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date

# ===================================================================
# NOVOS SCHEMAS (Substituindo os imports de report_models)
# ===================================================================

class DashboardKPIs(BaseModel):
    """KPIs principais do topo do dashboard."""
    total_machines: int
    available_machines: int
    in_use_machines: int
    maintenance_machines: int
    # Mantidos para compatibilidade, mas podem ser 0
    total_distance: float = 0.0
    total_fuel: float = 0.0

class CostByCategory(BaseModel):
    """Estrutura para o gráfico de custos."""
    category: str
    value: float

class UpcomingMaintenance(BaseModel):
    """Estrutura para lista de manutenções."""
    id: int
    machine_name: str
    description: str
    date: date 
    status: str

# ===================================================================
# SCHEMAS DO GESTOR
# ===================================================================

class KpiEfficiency(BaseModel):
    """KPIs focados em OEE (Indústria)."""
    availability: float
    performance: float
    quality: float
    oee: float

class AlertSummary(BaseModel):
    id: int
    type: str # Info, Warning, Error
    message: str
    timestamp: datetime
    machine_name: str

class GoalStatus(BaseModel):
    title: str
    current_value: float
    target_value: float
    unit: str

# --- Resposta Principal para o Dashboard do Gestor ---

class ManagerDashboardResponse(BaseModel):
    """Schema completo para a resposta do endpoint do dashboard."""
    kpis: DashboardKPIs
    efficiency_kpis: KpiEfficiency
    
    costs_by_category: List[CostByCategory] = []
    
    recent_alerts: List[AlertSummary] = []
    upcoming_maintenances: List[UpcomingMaintenance] = []
    active_goal: Optional[GoalStatus] = None

# ===================================================================
# SCHEMAS DO MOTORISTA / OPERADOR
# ===================================================================

class ActiveJourneyInfo(BaseModel):
    id: int
    machine_identifier: str
    start_time: datetime
    current_km_or_hour: float
    class Config:
        from_attributes = True

class DriverMetrics(BaseModel):
    distance: float
    hours: float
    fuel_efficiency: float
    alerts: int

class DriverRankEntry(BaseModel):
    rank: int
    name: str
    metric: float
    is_current_user: bool

class AchievementStatus(BaseModel):
    title: str
    icon: str
    unlocked: bool

class DriverDashboardResponse(BaseModel):
    metrics: DriverMetrics
    ranking_context: List[DriverRankEntry]
    achievements: List[AchievementStatus]
    active_journey: Optional[ActiveJourneyInfo] = None