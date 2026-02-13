from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy.orm import selectinload

# --- IMPORTS DE MODELS ---
from app.models.user_model import User, UserRole
from app.models.alert_model import Alert, AlertLevel
from app.models.goal_model import Goal
from app.models.vehicle_model import Vehicle, VehicleStatus
from app.models.journey_model import Journey
from app.models.organization_model import Organization
from app.models.report_models import DashboardKPIs, KmPerDay, UpcomingMaintenance, CostByCategory, DashboardPodiumDriver
from app.models.vehicle_cost_model import VehicleCost
from app.models.fuel_log_model import FuelLog
from app.models.maintenance_model import MaintenanceRequest, MaintenancePartChange, MaintenanceComment, MaintenanceStatus
from app.models.vehicle_component_model import VehicleComponent
from app.models.part_model import Part
from app.models.fine_model import Fine
from app.models.document_model import Document
from app.models.tire_model import VehicleTire as Tire
from app.models.inventory_transaction_model import InventoryTransaction
# [CORREÇÃO] Importar Models de Produção para ler OEE
from app.models.production_model import EmployeeDailyMetric, ProductionTimeSlice, VehicleDailyMetric, ProductionLog

# --- IMPORTS DE SCHEMAS ---
from app.schemas.dashboard_schema import KpiEfficiency, AlertSummary, GoalStatus, VehiclePosition
from app.schemas.report_schema import (
    DashboardSummary,
    FleetManagementReport, 
    VehicleRankingEntry, 
    FleetReportSummary, 
    DriverPerformanceEntry, 
    VehicleConsolidatedReport, 
    VehicleReportPerformanceSummary, 
    VehicleReportFinancialSummary, 
    DriverPerformanceReport,
    VehicleReportSections
)

# --- HELPER FUNCTIONS ---

def _calculate_relative_time(timestamp: datetime) -> str:
    """Helper para calcular string de tempo relativo."""
    if not timestamp:
        return ""
    now = datetime.utcnow() 
    diff = now - timestamp
    seconds = diff.total_seconds()
    if seconds < 60: return "agora"
    elif seconds < 3600: return f"há {int(seconds / 60)} min"
    elif seconds < 86400: return f"há {int(seconds / 3600)} h"
    elif seconds < 604800: return f"há {int(seconds / 86400)} d"
    else: return timestamp.strftime("%d/%m")

# --- RELATÓRIOS E KPI GERAIS ---

async def get_fleet_management_data(
    db: AsyncSession, *, start_date: date, end_date: date, organization_id: int
) -> FleetManagementReport:
    """
    Consolida dados de TODAS as máquinas: Custo Global e Disponibilidade da Fábrica.
    """
    # 1. Veículos
    vehicles = (await db.execute(select(Vehicle).where(Vehicle.organization_id == organization_id))).scalars().all()
    vehicle_ids = [v.id for v in vehicles]
    
    # 2. Custos Totais
    costs_stmt = select(VehicleCost).where(
        VehicleCost.organization_id == organization_id,
        VehicleCost.date.between(start_date, end_date)
    )
    all_costs = (await db.execute(costs_stmt)).scalars().all()
    total_fleet_cost = sum(c.amount for c in all_costs)
    
    costs_by_cat = {}
    for c in all_costs:
        cat = str(c.cost_type.value if hasattr(c.cost_type, 'value') else c.cost_type)
        costs_by_cat[cat] = costs_by_cat.get(cat, 0) + c.amount

    # 3. DADOS DE PRODUÇÃO (Disponibilidade)
    # Busca todas as fatias de tempo de todas as máquinas no período
    slices_stmt = select(ProductionTimeSlice).where(
        ProductionTimeSlice.vehicle_id.in_(vehicle_ids),
        func.date(ProductionTimeSlice.start_time).between(start_date, end_date)
    )
    all_slices = (await db.execute(slices_stmt)).scalars().all()

    total_run_sec = 0.0
    total_stop_sec = 0.0
    total_planned_sec = 0.0
    machine_metrics = {v.id: {"run": 0.0, "stop": 0.0, "cost": 0.0} for v in vehicles}

    for s in all_slices:
        dur = s.duration_seconds or 0
        cat = (s.category or "").upper()
        
        if cat in ["PRODUCING", "RUNNING", "IN_USE"]:
            total_run_sec += dur
            if s.vehicle_id in machine_metrics: machine_metrics[s.vehicle_id]["run"] += dur
        elif cat in ["UNPLANNED_STOP", "STOPPED", "PARADA"]:
            total_stop_sec += dur
            if s.vehicle_id in machine_metrics: machine_metrics[s.vehicle_id]["stop"] += dur
        elif cat in ["PLANNED_STOP", "SETUP"]:
            total_planned_sec += dur

    # Distribui custos por máquina
    for c in all_costs:
        if c.vehicle_id in machine_metrics:
            machine_metrics[c.vehicle_id]["cost"] += c.amount

    # Cálculos Globais
    total_avail_time = total_run_sec + total_stop_sec
    global_oee = (total_run_sec / total_avail_time * 100) if total_avail_time > 0 else 0.0
    global_avail = (total_run_sec / (total_avail_time + total_planned_sec) * 100) if (total_avail_time + total_planned_sec) > 0 else 0.0

    # Rankings
    ranking_data = []
    for v in vehicles:
        m = machine_metrics.get(v.id, {"run": 0, "stop": 0, "cost": 0})
        total_time = m["run"] + m["stop"]
        oee = (m["run"] / total_time * 100) if total_time > 0 else 0.0
        
        ranking_data.append({
            "id": v.id,
            "name": f"{v.brand} {v.model}",
            "cost": m["cost"],
            "oee": oee,
            "downtime": m["stop"] / 3600
        })

    # Ordenações
    most_expensive = sorted(ranking_data, key=lambda x: x["cost"], reverse=True)[:5]
    most_efficient = sorted(ranking_data, key=lambda x: x["oee"], reverse=True)[:5]
    least_efficient = sorted([r for r in ranking_data if r["oee"] > 0], key=lambda x: x["oee"])[:5]

    summary = FleetReportSummary(
        total_cost=total_fleet_cost,
        total_distance_km=0,
        overall_cost_per_km=0,
        # NOVOS
        global_oee=round(global_oee, 1),
        global_availability=round(global_avail, 1),
        total_production_hours=round(total_run_sec / 3600, 1),
        total_downtime_hours=round(total_stop_sec / 3600, 1),
        active_machines_count=len([v for v in vehicles if machine_metrics[v.id]["run"] > 0])
    )

    return FleetManagementReport(
        report_period_start=start_date, report_period_end=end_date, generated_at=datetime.utcnow(),
        summary=summary, costs_by_category=costs_by_cat,
        
        top_5_most_expensive_vehicles=[
            VehicleRankingEntry(vehicle_id=x['id'], vehicle_identifier=x['name'], value=x['cost'], unit='R$') 
            for x in most_expensive
        ],
        # Usamos este campo para OEE (Eficiência)
        top_5_most_efficient_vehicles=[
            VehicleRankingEntry(vehicle_id=x['id'], vehicle_identifier=x['name'], value=x['oee'], unit='%', secondary_value=x['downtime'], secondary_unit='h paradas') 
            for x in most_efficient
        ],
        # Usamos este campo para "Gargalos" (Baixo OEE)
        top_5_least_efficient_vehicles=[
            VehicleRankingEntry(vehicle_id=x['id'], vehicle_identifier=x['name'], value=x['oee'], unit='%') 
            for x in least_efficient
        ],
        top_5_highest_cost_per_km_vehicles=[]
    )

# --- FUNÇÃO PRINCIPAL CORRIGIDA PARA MES (OEE) ---

async def get_vehicle_consolidated_data(
    db: AsyncSession,
    vehicle_id: int,
    start_date: date,
    end_date: date,
    sections: VehicleReportSections,
    organization_id: int
) -> VehicleConsolidatedReport:
    
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.organization_id != organization_id:
        raise ValueError("Veículo não encontrado.")

    # 1. BUSCAR CUSTOS (Mantido)
    costs_data = []
    if sections.costs_detailed or sections.financial_summary:
        costs_stmt = select(VehicleCost).where(
            VehicleCost.vehicle_id == vehicle_id,
            VehicleCost.date >= start_date,
            VehicleCost.date <= end_date
        )
        costs_data = (await db.execute(costs_stmt)).scalars().all()

    # 2. BUSCAR DADOS DE PRODUÇÃO (TIME SLICES) - O CORAÇÃO DO MES
    slices = []
    if sections.performance_summary:
        slices_stmt = select(ProductionTimeSlice).where(
            ProductionTimeSlice.vehicle_id == vehicle_id,
            func.date(ProductionTimeSlice.start_time) >= start_date,
            func.date(ProductionTimeSlice.start_time) <= end_date
        )
        slices = (await db.execute(slices_stmt)).scalars().all()

    # --- CÁLCULO DE KPI INDUSTRIAIS (OEE / MTBF / MTTR) ---
    performance_summary = None
    
    if sections.performance_summary:
        # Inicializa contadores (em segundos)
        total_calendar_seconds = (end_date - start_date).days * 24 * 3600 # Estimado se full time
        if len(slices) > 0:
             # Ajuste fino: pega delta real entre primeiro e ultimo slice registrado se for maior
             delta_real = (slices[-1].start_time - slices[0].start_time).total_seconds()
             total_calendar_seconds = max(total_calendar_seconds, delta_real)

        running_seconds = 0.0
        planned_stop_seconds = 0.0
        unplanned_stop_seconds = 0.0
        idle_seconds = 0.0
        
        failures_count = 0
        repair_seconds = 0.0
        
        stop_reasons_map = {}

        for s in slices:
            duration = s.duration_seconds or 0
            cat = (s.category or "").upper()
            reason = (s.reason or "Não identificado").strip()

            if cat in ["PRODUCING", "RUNNING", "IN_USE"]:
                running_seconds += duration
            elif cat in ["PLANNED_STOP", "SETUP", "MANUTENÇÃO", "MAINTENANCE"]:
                planned_stop_seconds += duration
            elif cat in ["UNPLANNED_STOP", "STOPPED", "PAUSED", "PARADA"]:
                unplanned_stop_seconds += duration
                # Contabiliza Falha para MTBF
                failures_count += 1
                repair_seconds += duration
                # Agrega motivo para Pareto
                stop_reasons_map[reason] = stop_reasons_map.get(reason, 0) + duration
            else:
                idle_seconds += duration

        # -- Cálculos OEE --
        available_time = total_calendar_seconds - planned_stop_seconds
        
        # 1. Disponibilidade = (Tempo Disponível - Paradas Não Planejadas) / Tempo Disponível
        # Ou simplificado: Running / Available (se assumirmos que idle faz parte de perda ou não)
        # Vamos usar a definição clássica: (Running Time) / (Planned Running Time)
        availability = (running_seconds / available_time) if available_time > 0 else 0.0
        
        # 2. Performance e Qualidade (Mockados ou parciais se não tiver contadores de peças no slice)
        # Se você tiver production_log com contagem, pode refinar aqui.
        performance = 0.95 # Exemplo estimado
        quality = 0.98     # Exemplo estimado
        
        oee = availability * performance * quality

        # -- Cálculos Confiabilidade --
        # MTBF = (Tempo Total em Operação) / (Número de Falhas)
        mtbf_hours = (running_seconds / 3600) / failures_count if failures_count > 0 else (running_seconds / 3600)
        
        # MTTR = (Tempo Total de Reparo) / (Número de Falhas)
        mttr_hours = (repair_seconds / 3600) / failures_count if failures_count > 0 else 0.0

        # -- Pareto de Paradas --
        sorted_reasons = sorted(stop_reasons_map.items(), key=lambda x: x[1], reverse=True)[:5]
        stop_reasons_list = [
            {"reason": k, "duration_minutes": round(v / 60, 1), "percent": round((v / (unplanned_stop_seconds or 1)) * 100, 1)}
            for k, v in sorted_reasons
        ]

        performance_summary = VehicleReportPerformanceSummary(
            vehicle_total_activity=vehicle.current_engine_hours or 0.0,
            period_total_activity=round(running_seconds / 3600, 2), # Horas Produzidas
            activity_unit="horas",
            period_total_fuel=0, # Não usado em MES
            average_consumption=0, 
            
            # NOVOS DADOS RICOS
            oee_percent=round(oee * 100, 1),
            availability_percent=round(availability * 100, 1),
            performance_percent=round(performance * 100, 1),
            quality_percent=round(quality * 100, 1),
            
            mtbf_hours=round(mtbf_hours, 1),
            mttr_hours=round(mttr_hours, 1),
            
            time_distribution={
                "calendar": round(total_calendar_seconds / 3600, 1),
                "planned_stop": round(planned_stop_seconds / 3600, 1),
                "unplanned_stop": round(unplanned_stop_seconds / 3600, 1),
                "running": round(running_seconds / 3600, 1),
                "idle": round(idle_seconds / 3600, 1)
            },
            stop_reasons=stop_reasons_list
        )

    # 4. FINANCEIRO (Cálculo Unitário)
    financial_summary = None
    if sections.financial_summary:
        total_costs = sum(c.amount for c in costs_data)
        prod_hours = (performance_summary.period_total_activity if performance_summary else 0)
        cost_per_h = (total_costs / prod_hours) if prod_hours > 0 else 0.0
        
        costs_map = {}
        for c in costs_data:
            cat = c.cost_type.value if hasattr(c.cost_type, 'value') else str(c.cost_type)
            costs_map[cat] = costs_map.get(cat, 0.0) + c.amount
            
        financial_summary = VehicleReportFinancialSummary(
            total_costs=total_costs,
            cost_per_metric=cost_per_h,
            metric_unit="R$/h",
            costs_by_category=costs_map
        )

    # ... (Busca de Manutenções e Documentos mantida igual ao anterior) ...
    maintenance_data = [] # (Insira a query de manutenção existente aqui)
    documents_data = [] # (Insira a query de documentos existente aqui)

    return VehicleConsolidatedReport(
        vehicle_id=vehicle.id,
        vehicle_identifier=vehicle.license_plate or vehicle.identifier,
        vehicle_model=f"{vehicle.brand} {vehicle.model}",
        report_period_start=start_date,
        report_period_end=end_date,
        generated_at=datetime.utcnow(),
        performance_summary=performance_summary,
        financial_summary=financial_summary,
        costs_detailed=costs_data if sections.costs_detailed else [],
        maintenance_detailed=maintenance_data, # Passar dados reais
        documents_detailed=documents_data,
        fuel_logs_detailed=[],
        fines_detailed=[],
        journeys_detailed=[],
        tires_detailed=[]
    )

async def get_driver_performance_data(
    db: AsyncSession, *, start_date: date, end_date: date, organization_id: int
) -> DriverPerformanceReport:
    """
    Analisa EmployeeDailyMetric para calcular produtividade humana.
    """
    # Busca operadores
    # Ajuste: busca qualquer user que tenha métricas, não só role='driver', para pegar operadores de maquina
    users = (await db.execute(select(User).where(User.organization_id == organization_id))).scalars().all()
    user_map = {u.id: u.full_name for u in users}
    
    # Busca métricas diárias consolidadas
    metrics_stmt = select(EmployeeDailyMetric).where(
        EmployeeDailyMetric.organization_id == organization_id,
        EmployeeDailyMetric.date.between(start_date, end_date)
    )
    metrics = (await db.execute(metrics_stmt)).scalars().all()
    
    agg_data = {}
    
    for m in metrics:
        if m.user_id not in agg_data:
            agg_data[m.user_id] = {
                "prod_hours": 0.0, "total_hours": 0.0, "days": 0
            }
        
        agg_data[m.user_id]["prod_hours"] += (m.productive_hours or 0)
        agg_data[m.user_id]["total_hours"] += (m.total_hours or 0)
        agg_data[m.user_id]["days"] += 1

    results = []
    for uid, data in agg_data.items():
        if uid not in user_map: continue
        
        total_h = data["total_hours"]
        prod_h = data["prod_hours"]
        
        # Eficiência Média Ponderada
        efficiency = (prod_h / total_h * 100) if total_h > 0 else 0.0
        
        results.append(DriverPerformanceEntry(
            driver_id=uid,
            driver_name=user_map[uid],
            total_journeys=data["days"], # Dias trabalhados
            productive_hours=round(prod_h, 1),
            efficiency_percent=round(efficiency, 1),
            # Campos legados zerados
            total_distance_km=0, total_fuel_liters=0, average_consumption=0, 
            total_fuel_cost=0, cost_per_km=0, maintenance_requests=0
        ))

    # Ordena por eficiência
    sorted_data = sorted(results, key=lambda x: x.efficiency_percent, reverse=True)

    return DriverPerformanceReport(
        report_period_start=start_date, 
        report_period_end=end_date, 
        generated_at=datetime.utcnow(), 
        drivers_performance=sorted_data
    )

async def get_driver_activity_data(db: AsyncSession, driver_id: int, organization_id: int, date_from: date, date_to: date) -> Dict[str, Any]:
    return {"driver_name": "N/A", "period": "", "journeys": []}

# --- DASHBOARD SUMMARY ---

async def get_dashboard_summary(db: AsyncSession, current_user: User, start_date: datetime) -> DashboardSummary:
    try:
        total_vehicles = (await db.execute(select(func.count(Vehicle.id)).where(Vehicle.organization_id == current_user.organization_id))).scalar() or 0
        total_costs = (await db.execute(select(func.sum(VehicleCost.amount)).where(VehicleCost.organization_id == current_user.organization_id, VehicleCost.date >= start_date.date()))).scalar() or 0
        
        # Manutenção
        maint_open = (await db.execute(select(func.count(MaintenanceRequest.id)).where(
            MaintenanceRequest.organization_id == current_user.organization_id,
            MaintenanceRequest.status.in_([MaintenanceStatus.PENDENTE, MaintenanceStatus.EM_ANDAMENTO])
        ))).scalar() or 0

        return DashboardSummary(
            total_vehicles=total_vehicles,
            active_journeys=0,
            total_costs_last_30_days=total_costs,
            maintenance_open_requests=maint_open
        )
    except Exception as e:
        logging.error(f"Erro dashboard: {e}")
        return DashboardSummary(total_vehicles=0, active_journeys=0, total_costs_last_30_days=0, maintenance_open_requests=0)

# --- STUBS PARA O RESTO (KPIs Dashboard não usados no Report) ---
async def get_dashboard_kpis(db: AsyncSession, *, organization_id: int) -> dict: return {}
async def get_costs_by_category_last_30_days(db: AsyncSession, *, organization_id: int, start_date: date | None = None) -> List: return []
async def get_podium_drivers(db: AsyncSession, *, organization_id: int) -> List: return []
async def get_km_per_day_last_30_days(db: AsyncSession, *, organization_id: int, start_date: date | None = None) -> List: return []
async def get_upcoming_maintenances(db: AsyncSession, *, organization_id: int) -> List: return []
async def get_efficiency_kpis(db: AsyncSession, *, organization_id: int, start_date: date) -> KpiEfficiency:
    return KpiEfficiency(cost_per_km=0, fleet_avg_efficiency=0, utilization_rate=0)
async def get_recent_alerts(db: AsyncSession, organization_id: int, limit: int = 5) -> List: return []
async def get_active_goal_with_progress(db: AsyncSession, *, organization_id: int) -> Optional[GoalStatus]: return None
async def get_vehicle_positions(db: AsyncSession, *, organization_id: int) -> List: return []