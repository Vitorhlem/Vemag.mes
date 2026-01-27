from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from .vehicle_cost_schema import VehicleCostPublic
from .fuel_log_schema import FuelLogPublic
from .maintenance_schema import MaintenanceRequestPublic
# --- NOVOS IMPORTS ---
from .fine_schema import FinePublic
from .journey_schema import JourneyPublic
from .document_schema import DocumentPublic
from .tire_schema import VehicleTirePublic as TirePublic

# Mantém o schema do dashboard existente
class DashboardSummary(BaseModel):
    total_vehicles: int
    active_journeys: int
    total_costs_last_30_days: float
    maintenance_open_requests: int

# --- NOVOS SCHEMAS PARA O PEDIDO DO RELATÓRIO ---

class VehicleReportSections(BaseModel):
    """Define quais seções devem ser incluídas no relatório."""
    performance_summary: bool = True
    financial_summary: bool = True
    costs_detailed: bool = True
    fuel_logs_detailed: bool = True
    maintenance_detailed: bool = False
    fines_detailed: bool = False
    journeys_detailed: bool = False
    documents_detailed: bool = False
    tires_detailed: bool = False

class VehicleReportRequest(BaseModel):
    """Schema para o corpo (body) do pedido do relatório consolidado."""
    vehicle_id: int
    start_date: date
    end_date: date
    sections: VehicleReportSections

# --- SCHEMAS DE RESPOSTA ATUALIZADOS ---

class VehicleReportPerformanceSummary(BaseModel):
    vehicle_total_activity: float
    period_total_activity: float
    activity_unit: str
    period_total_fuel: float
    average_consumption: float
    
    # --- NOVOS CAMPOS PARA OEE & CONFIABILIDADE ---
    oee_percent: float = 0.0
    availability_percent: float = 0.0
    performance_percent: float = 0.0
    quality_percent: float = 0.0
    
    mtbf_hours: float = 0.0
    mttr_hours: float = 0.0
    
    # Dados para Gráficos
    time_distribution: Dict[str, float] = {} # Ex: {"total": 720, "running": 500...}
    stop_reasons: List[Dict[str, Any]] = []  # Ex: [{"reason": "Quebra", "duration": 200}]

class VehicleReportFinancialSummary(BaseModel):
    """Resumo financeiro para o relatório."""
    total_costs: float = 0.0
    cost_per_metric: float = 0.0       # Renomeado de cost_per_km
    cost_per_metric_unit: str = "km"   # Novo campo
    costs_by_category: Dict[str, float] = {}

class VehicleConsolidatedReport(BaseModel):
    """Schema principal para o Relatório Consolidado de Veículo."""
    # --- Dados de Cabeçalho ---
    vehicle_id: int
    vehicle_identifier: str 
    vehicle_model: str
    report_period_start: date
    report_period_end: date
    generated_at: datetime

    # --- Seções de Dados (Agora Opcionais) ---
    performance_summary: Optional[VehicleReportPerformanceSummary] = None
    financial_summary: Optional[VehicleReportFinancialSummary] = None
    
    # --- Dados Detalhados (Agora Opcionais) ---
    costs_detailed: Optional[List[VehicleCostPublic]] = None
    fuel_logs_detailed: Optional[List[FuelLogPublic]] = None
    maintenance_detailed: Optional[List[MaintenanceRequestPublic]] = None
    fines_detailed: Optional[List[FinePublic]] = None
    journeys_detailed: Optional[List[JourneyPublic]] = None
    documents_detailed: Optional[List[DocumentPublic]] = None
    tires_detailed: Optional[List[TirePublic]] = None
    
    class Config:
        from_attributes = True

# --- Schemas de outros relatórios (sem alteração) ---

class DriverPerformanceEntry(BaseModel):
    driver_id: int
    driver_name: str
    
    # Campos Logísticos (Legado/Híbrido)
    total_journeys: int = 0
    total_distance_km: float = 0
    total_fuel_liters: float = 0
    average_consumption: float = 0
    total_fuel_cost: float = 0
    cost_per_km: float = 0
    maintenance_requests: int = 0
    
    # NOVOS CAMPOS MES (Chão de Fábrica)
    productive_hours: float = 0.0
    efficiency_percent: float = 0.0 # OEE Pessoal
    items_produced: int = 0
class DriverPerformanceReport(BaseModel):
    """Schema principal para o Relatório de Desempenho de Motoristas."""
    report_period_start: date
    report_period_end: date
    generated_at: datetime
    drivers_performance: List[DriverPerformanceEntry]

    class Config:
        from_attributes = True

class FleetReportSummary(BaseModel):
    total_cost: float
    total_distance_km: float # Mantido para compatibilidade
    overall_cost_per_km: float
    
    # NOVOS CAMPOS MES
    global_oee: float = 0.0
    global_availability: float = 0.0
    total_production_hours: float = 0.0
    total_downtime_hours: float = 0.0
    active_machines_count: int = 0
    
class VehicleRankingEntry(BaseModel):
    vehicle_id: int
    vehicle_identifier: str
    value: float
    unit: str
    secondary_value: Optional[float] = None # Ex: Custo (Principal) + OEE (Secundário)
    secondary_unit: Optional[str] = None

class FleetManagementReport(BaseModel):
    """Schema principal para o Relatório Gerencial da Frota."""
    report_period_start: date
    report_period_end: date
    generated_at: datetime
    
    summary: FleetReportSummary
    costs_by_category: Dict[str, float] = {}
    
    # Rankings
    top_5_most_expensive_vehicles: List[VehicleRankingEntry]
    top_5_highest_cost_per_km_vehicles: List[VehicleRankingEntry]
    top_5_most_efficient_vehicles: List[VehicleRankingEntry]
    top_5_least_efficient_vehicles: List[VehicleRankingEntry]

    class Config:
        from_attributes = True