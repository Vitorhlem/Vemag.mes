from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, date, time, timedelta
from typing import Any, List, Optional
from pydantic import BaseModel
from app.tasks.production_tasks import process_sap_appointment

# Imports do Projeto
from app.db.session import get_db, async_session
from app import deps
from app.models.production_model import ProductionAppointment, VehicleDailyMetric, EmployeeDailyMetric, ProductionOrder, ProductionSession, ProductionLog, AndonAlert, ProductionTimeSlice
from app.models.user_model import User, UserRole
from app.services.fcm_service import enviar_push_lista
from app.services.production_service import ProductionService
from app.services.sap_sync import SAPIntegrationService
from app.schemas import production_schema, vehicle_schema, user_schema
from app.schemas.production_schema import SessionStart, SessionResponse, AppointmentCreate, EmployeeStatsRead, ProductionAppointmentCreate, ProductionOrderRead, MachineDailyStats

# Import do Modelo Vehicle (com fallback de nome)
try:
    from app.models.vehicle_model import Vehicle, VehicleStatus
except ImportError:
    from app.models.vehicle import Vehicle, VehicleStatus

router = APIRouter()

# --- MODEL LOCAL ---
class MachineStatusUpdate(BaseModel):
    machine_id: int
    status: str

class MachineStatsRealTime(BaseModel):
    date: str
    total_running_operator_seconds: float
    total_running_autonomous_seconds: float
    total_paused_operator_seconds: float
    total_maintenance_seconds: float
    total_micro_stop_seconds: float
    total_idle_seconds: float
    total_setup_seconds: float
    total_pause_seconds: float
    formatted_running_operator: str
    formatted_running_autonomous: str
    formatted_paused_operator: str
    formatted_maintenance: str
    formatted_setup: str
    formatted_pause: str
    formatted_micro_stop: str


# ============================================================================
# 0. ESTATÍSTICAS DE FUNCIONÁRIOS
# ============================================================================

@router.post("/closing/force")
async def force_daily_closing(
    target_date: date = None, 
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Força o cálculo e persistência das métricas para uma data específica."""
    if not target_date: target_date = date.today()
    
    users_count = await ProductionService.consolidate_daily_metrics(db, target_date)
    machines_count = await ProductionService.consolidate_machine_metrics(db, target_date)
    
    return {
        "message": "Fechamento Completo executado", 
        "date": target_date, 
        "processed": {"users": users_count, "machines": machines_count}
    }

@router.get("/reports/daily-closing", response_model=List[Any])
async def get_daily_closing_report(
    target_date: date,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    org_id = current_user.organization_id if current_user else 1
    
    query = select(EmployeeDailyMetric).where(
        EmployeeDailyMetric.date == target_date,
        EmployeeDailyMetric.organization_id == org_id
    ).order_by(desc(EmployeeDailyMetric.total_hours))
    
    query = query.options(selectinload(EmployeeDailyMetric.user))
    results = (await db.execute(query)).scalars().all()
    
    report_data = []
    for row in results:
        report_data.append({
            "id": row.id,
            "user_id": row.user_id,
            "employee_name": row.user.full_name if row.user else f"ID {row.user_id}",
            "total_hours": row.total_hours,
            "productive_hours": row.productive_hours,
            "unproductive_hours": row.unproductive_hours,
            "efficiency": row.efficiency,
            "top_reasons": row.top_reasons_snapshot,
            "closed_at": row.closed_at
        })
    return report_data

@router.get("/stats/employees", response_model=List[EmployeeStatsRead])
async def get_employee_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_active_user)
):
    if not start_date: start_date = date.today().replace(day=1)
    if not end_date: end_date = date.today()
        
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)
    
    org_id = current_user.organization_id if current_user else 1
    query_users = select(User).where(User.organization_id == org_id)
    users = (await db.execute(query_users)).scalars().all()
    
    stats_list = []

    for user in users:
        op_id_str = str(user.id) 
        
        q_logs = select(ProductionLog).where(
            ProductionLog.operator_id == user.id,
            
            ProductionLog.timestamp >= dt_start,
            ProductionLog.timestamp <= dt_end
        ).order_by(ProductionLog.vehicle_id, ProductionLog.timestamp)
        
        user_logs = (await db.execute(q_logs)).scalars().all()
        
        if not user_logs:
            stats_list.append({
                "id": user.id, "employee_name": user.full_name or user.email,
                "total_hours": 0, "productive_hours": 0, "unproductive_hours": 0,
                "efficiency": 0, "top_reasons": []
            })
            continue

        prod_sec = 0.0
        unprod_sec = 0.0
        reasons_map = {}

        for log in user_logs:
            q_next = select(ProductionLog).where(
                ProductionLog.vehicle_id == log.vehicle_id,
                ProductionLog.timestamp > log.timestamp
            ).order_by(ProductionLog.timestamp.asc()).limit(1)
            
            next_log = (await db.execute(q_next)).scalars().first()
            end_time = next_log.timestamp if next_log else datetime.now()
            
            duration = (end_time - log.timestamp).total_seconds()
            if duration > 43200: duration = 0 
            if duration < 0: duration = 0

            st = (log.new_status or "").upper()
            reason = (log.reason or "").upper()
            
            is_running = st in ["RUNNING", "EM OPERAÇÃO", "EM USO", "PRODUCING", "IN_USE", "PRODUÇÃO AUTÔNOMA", "IN_USE_AUTONOMOUS"]
            is_setup = "SETUP" in st or "SETUP" in reason or "PREPARAÇÃO" in reason
            
            if is_running or is_setup:
                prod_sec += duration
            else:
                unprod_sec += duration
                if duration > 60:
                    lbl = log.reason or st or "Parada genérica"
                    reasons_map[lbl] = reasons_map.get(lbl, 0) + 1

        total_sec = prod_sec + unprod_sec
        efficiency = (prod_sec / total_sec * 100) if total_sec > 0 else 0.0
        
        sorted_reasons = sorted(reasons_map.items(), key=lambda x: x[1], reverse=True)[:3]
        top_reasons_list = [{"label": k, "count": v} for k, v in sorted_reasons]

        stats_list.append({
            "id": user.id, 
            "employee_name": user.full_name or user.email,
            "total_hours": round(total_sec / 3600, 2),
            "productive_hours": round(prod_sec / 3600, 2),
            "unproductive_hours": round(unprod_sec / 3600, 2),
            "efficiency": round(efficiency, 1),
            "top_reasons": top_reasons_list
        })
    
    stats_list.sort(key=lambda x: x['total_hours'], reverse=True)
    return stats_list

# ============================================================================
# 1. ESTATÍSTICAS DA MÁQUINA (CORRIGIDO PARA NOVA ARQUITETURA)
# ============================================================================
@router.get("/stats/{machine_id}", response_model=MachineStatsRealTime)
async def get_machine_stats(machine_id: int, target_date: date = None, db: AsyncSession = Depends(get_db)):
    if not target_date: target_date = date.today()
    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)
    if target_date == date.today(): end_of_day = datetime.now()

    # 1. VERIFICA SESSÃO ATIVA
    q_session = select(ProductionSession).where(
        ProductionSession.vehicle_id == machine_id,
        ProductionSession.start_time < start_of_day,
        or_(ProductionSession.end_time == None, ProductionSession.end_time >= start_of_day)
    )
    active_session_start = (await db.execute(q_session)).scalars().first()
    is_operator_present = active_session_start is not None

    # 2. STATUS INICIAL
    stmt_last_st = select(ProductionLog).filter(
        ProductionLog.vehicle_id == machine_id,
        ProductionLog.timestamp < start_of_day,
        ProductionLog.new_status.isnot(None)
    ).order_by(ProductionLog.timestamp.desc()).limit(1)
    
    last_st = (await db.execute(stmt_last_st)).scalars().first()
    current_status = last_st.new_status if last_st else "IDLE"
    current_reason = last_st.reason if last_st else ""

    # 3. LOGS DO DIA
    stmt_logs = select(ProductionLog).filter(
        ProductionLog.vehicle_id == machine_id,
        ProductionLog.timestamp >= start_of_day,
        ProductionLog.timestamp <= end_of_day
    ).order_by(ProductionLog.timestamp.asc())

    todays_logs = (await db.execute(stmt_logs)).scalars().all()

    stats = {"running_op": 0.0, "running_auto": 0.0, "setup": 0.0, "pause": 0.0, "micro_stop": 0.0, "maintenance": 0.0, "idle": 0.0}
    timeline = []
    timeline.append({"time": start_of_day, "status": current_status, "has_op": is_operator_present, "reason": current_reason})

    for log in todays_logs:
        # ✅ NOVA LÓGICA: Se o operator_id não for nulo, tem um humano na máquina
        if log.operator_id is not None:
            is_operator_present = True
        
        # Se houver um evento de saída, marcamos como ausente
        if log.event_type in ['LOGOUT', 'SESSION_END', 'LOGOFF']:
            is_operator_present = False
        
        if log.new_status: 
            current_status = log.new_status
        if log.reason: 
            current_reason = log.reason

        timeline.append({
            "time": log.timestamp,
            "status": current_status,
            "has_op": is_operator_present,
            "reason": current_reason
        })

    timeline.append({"time": end_of_day, "status": "IGNORE", "has_op": is_operator_present, "reason": ""})

    # --- CÁLCULO (NOVA LÓGICA DE ESTADOS) ---
    for i in range(len(timeline) - 1):
        seg = timeline[i]
        duration = (timeline[i+1]["time"] - seg["time"]).total_seconds()
        if duration <= 0: continue
        
        st = str(seg["status"]).upper()
        reason = str(seg.get("reason") or "").upper() 
        op = seg["has_op"]

        # 1. MANUTENÇÃO (Card Vermelho)
        if st in ["MAINTENANCE", "EM MANUTENÇÃO", "QUEBRADA"]:
            stats["maintenance"] += duration
        
        # 2. SETUP (Card Roxo - Explícito)
        elif st in ["SETUP", "PREPARAÇÃO"]:
            stats["setup"] += duration

        # 3. PRODUÇÃO (Verde ou Azul)
        elif st in ["RUNNING", "EM OPERAÇÃO", "EM USO", "PRODUCING", "1", "IN_USE", "PRODUÇÃO AUTÔNOMA", "IN_USE_AUTONOMOUS"]:
            # Se for explicitamente autônomo OU se não tiver operador
            if "AUTÔNOMA" in st or "AUTONOMOUS" in st:
                stats["running_auto"] += duration
            elif op: 
                stats["running_op"] += duration 
            else: 
                stats["running_auto"] += duration 
        
        # 4. PARADAS E OCIOSIDADE
        elif st in ["PAUSED", "PARADA", "STOPPED", "AVAILABLE", "IDLE", "PAUSADA", "0", "OCIOSO", "OCIOSIDADE", "DISPONÍVEL"]:
            
            # Prioridade 1: Sem motivo definido ou Status Ocioso -> CINZA
            if reason == "SEM MOTIVO" or st in ["OCIOSO", "OCIOSIDADE", "AVAILABLE", "DISPONÍVEL", "IDLE"]:
                stats["idle"] += duration 
            
            # Prioridade 2: Micro-paradas (< 5 min) -> AMARELO
            elif duration < 300:
                stats["micro_stop"] += duration
            
            # Prioridade 3: Parada com motivo (> 5 min) -> LARANJA
            else:
                stats["pause"] += duration
        
        else:
            stats["idle"] += duration

    def fmt(seconds):
        return str(timedelta(seconds=int(seconds)))

    return MachineStatsRealTime(
        date=str(target_date),
        total_running_operator_seconds=stats["running_op"],
        total_running_autonomous_seconds=stats["running_auto"],
        total_paused_operator_seconds=stats["pause"] + stats["micro_stop"],
        total_maintenance_seconds=stats["maintenance"],
        total_idle_seconds=stats["idle"],
        total_setup_seconds=stats["setup"],
        total_pause_seconds=stats["pause"],
        total_micro_stop_seconds=stats["micro_stop"],
        formatted_running_operator=fmt(stats["running_op"]),
        formatted_running_autonomous=fmt(stats["running_auto"]),
        formatted_paused_operator=fmt(stats["pause"] + stats["micro_stop"]),
        formatted_maintenance=fmt(stats["maintenance"]),
        formatted_setup=fmt(stats["setup"]),
        formatted_pause=fmt(stats["pause"]),
        formatted_micro_stop=fmt(stats["micro_stop"])
    )

@router.get("/stats/{machine_id}/history", response_model=List[production_schema.VehicleDailyMetricRead])
async def get_machine_history_metrics(machine_id: int, days: int = 90, db: AsyncSession = Depends(get_db)):
    start_date = date.today() - timedelta(days=days)
    query = select(VehicleDailyMetric).where(
        VehicleDailyMetric.vehicle_id == machine_id,
        VehicleDailyMetric.date >= start_date
    ).order_by(VehicleDailyMetric.date.asc())
    
    result = await db.execute(query)
    return result.scalars().all()

class MachinePeriodStats(BaseModel):
    total_running: float
    total_setup: float
    total_pause: float
    total_maintenance: float
    avg_availability: float
    stop_reasons: List[dict]

# --- BLOCO 3: ROTA DE AGREGAÇÃO PARA OS CARDS PROFISSIONAIS ---
@router.get("/stats/{machine_id}/period-summary", response_model=production_schema.MachinePeriodSummary)
async def get_machine_period_summary(machine_id: int, days: int = 30, db: AsyncSession = Depends(get_db)):
    today = date.today()
    start_date = today - timedelta(days=days)
    
    IGNORED_LABELS = [
        "PARADA", "PAUSED", "STOPPED", "AVAILABLE", "DISPONÍVEL", "IDLE", 
        "OUTROS", "UNDEFINED", "SEM MOTIVO", "AGUARDANDO INÍCIO", "PENDING",
        "LOGOFF", "TROCA DE TURNO", "LOGOFF / TROCA DE TURNO", "Manutenção Geral", "MANUTENÇÃO GERAL",
        "OCIOSO", "OCIOSIDADE", "SETUP", "PREPARAÇÃO"
    ]

    # ... (O restante da função de resumo permanece igual, pois ela usa a lógica do VehicleDailyMetric que já foi consolidada)
    # Apenas certifique-se de que a lógica de "Hoje" (Parte B) também use os novos status se necessário
    # Para brevidade, mantive o código original aqui, mas a lógica de IGNORED_LABELS acima já ajuda a limpar o gráfico.
    
    # ---------------------------------------------------------
    # PARTE B (HOJE) REVISADA RAPIDAMENTE PARA COMPATIBILIDADE
    # ---------------------------------------------------------
    start_of_today = datetime.combine(today, time.min)
    end_of_today = datetime.now()
    
    stmt_logs = select(ProductionLog).filter(
        ProductionLog.vehicle_id == machine_id,
        ProductionLog.timestamp >= start_of_today
    ).order_by(ProductionLog.timestamp.asc())
    todays_logs = (await db.execute(stmt_logs)).scalars().all()

    stmt_last = select(ProductionLog).filter(
        ProductionLog.vehicle_id == machine_id,
        ProductionLog.timestamp < start_of_today
    ).order_by(ProductionLog.timestamp.desc()).limit(1)
    last_log_before = (await db.execute(stmt_last)).scalars().first()

    current_status = last_log_before.new_status if last_log_before else "IDLE"
    current_reason = last_log_before.reason if last_log_before else ""
    
    timeline = []
    timeline.append({"time": start_of_today, "status": current_status, "reason": current_reason})
    for log in todays_logs:
        timeline.append({"time": log.timestamp, "status": log.new_status, "reason": log.reason})
    timeline.append({"time": end_of_today, "status": "IGNORE", "reason": ""})

    today_running, today_setup, today_pause, today_maintenance, today_micro = 0.0, 0.0, 0.0, 0.0, 0.0
    reasons_hours_map = {}

    for i in range(len(timeline) - 1):
        seg = timeline[i]
        duration_hours = (timeline[i+1]["time"] - seg["time"]).total_seconds() / 3600
        if duration_hours <= 0: continue

        st = str(seg["status"]).upper()
        reason_label = str(seg.get("reason") or "").strip()
        if not reason_label and st not in IGNORED_LABELS and st not in ["RUNNING", "EM USO", "EM OPERAÇÃO"]:
             reason_label = st

        if any(x in st for x in ["MAINTENANCE", "MANUTENÇÃO", "QUEBRADA"]):
            today_maintenance += duration_hours
            if reason_label and reason_label.upper() not in IGNORED_LABELS:
                reasons_hours_map[reason_label] = reasons_hours_map.get(reason_label, 0) + duration_hours
        
        elif any(x in st for x in ["RUNNING", "EM OPERAÇÃO", "EM USO", "IN_USE", "AUTÔNOMA", "AUTONOMOUS"]):
            today_running += duration_hours

        elif any(x in st for x in ["SETUP", "PREPARAÇÃO"]):
            today_setup += duration_hours

        else: # Paradas e Ociosidade
            if duration_hours < 0.083:
                today_micro += duration_hours
            else:
                today_pause += duration_hours
                if reason_label and reason_label.upper() not in IGNORED_LABELS:
                    reasons_hours_map[reason_label] = reasons_hours_map.get(reason_label, 0) + duration_hours

    # ... (Restante da função de agregação histórica continua igual)
    
    # ---------------------------------------------------------
    # PARTE A: DADOS HISTÓRICOS (REPITA A CONSULTA ORIGINAL)
    # ---------------------------------------------------------
    query_history = select(VehicleDailyMetric).where(
        VehicleDailyMetric.vehicle_id == machine_id,
        VehicleDailyMetric.date >= start_date,
        VehicleDailyMetric.date < today 
    )
    metrics_history = (await db.execute(query_history)).scalars().all()
    
    total_running = sum(m.running_hours for m in metrics_history)
    total_setup = sum(m.planned_stop_hours for m in metrics_history)
    total_pause = sum(m.idle_hours for m in metrics_history)
    total_maintenance = sum(m.maintenance_hours for m in metrics_history)
    total_micro_stops = sum(m.micro_stop_hours for m in metrics_history)
    
    for m in metrics_history:
        for entry in (m.top_reasons_snapshot or []):
            lbl = entry.get('label', '').strip()
            hours = float(entry.get('hours', 0))
            if not lbl or lbl.upper() in IGNORED_LABELS: continue
            reasons_hours_map[lbl] = reasons_hours_map.get(lbl, 0) + hours

    final_running = total_running + today_running
    final_setup = total_setup + today_setup
    final_pause = total_pause + today_pause
    final_maintenance = total_maintenance + today_maintenance
    final_micro = total_micro_stops + today_micro

    sum_avail_history = sum(m.availability for m in metrics_history)
    count_history = len(metrics_history)
    today_total_time = (end_of_today - start_of_today).total_seconds() / 3600
    today_avail_base = today_total_time - today_setup
    today_availability = (today_running / today_avail_base * 100) if today_avail_base > 0 else 0.0
    if today_availability > 100: today_availability = 100.0

    final_avg_availability = (sum_avail_history + today_availability) / (count_history + 1)

    sorted_stops = sorted([{"name": k, "value": round(v, 2)} for k, v in reasons_hours_map.items() if v > 0.01], key=lambda x: x['value'], reverse=True)
    avg_mtbf = round(sum(m.mtbf for m in metrics_history) / count_history, 1) if count_history > 0 else 0
    avg_mttr = round(sum(m.mttr for m in metrics_history) / count_history, 1) if count_history > 0 else 0

    return {
        "total_running": round(final_running, 1),
        "total_setup": round(final_setup, 1),
        "total_pause": round(final_pause, 1),
        "total_maintenance": round(final_maintenance, 1),
        "total_micro_stops": round(final_micro, 1),
        "avg_availability": round(final_avg_availability, 1),
        "stop_reasons": sorted_stops[:10],
        "mtbf": avg_mtbf,
        "mttr": avg_mttr
    }

@router.post("/consolidate/{machine_id}")
async def force_machine_consolidation(machine_id: int, db: AsyncSession = Depends(get_db)):
    try:
        processed_count = await ProductionService.consolidate_machine_metrics(db, date.today())
        return {"status": "success", "processed": processed_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

# ============================================================================
# 2. OPERADOR (Busca por Crachá)
# ============================================================================
@router.get("/operator/{badge}", response_model=user_schema.UserPublic)
async def get_operator_by_badge(badge: str, db: AsyncSession = Depends(deps.get_db)):
    clean_badge = badge.strip()
    query = select(User).options(selectinload(User.organization)).where(User.employee_id == clean_badge)
    user = (await db.execute(query)).scalars().first()
    
    if not user:
        query = select(User).options(selectinload(User.organization)).where(func.lower(User.email) == clean_badge.lower())
        user = (await db.execute(query)).scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Operador não encontrado.")
    return user

# ============================================================================
# 3. STATUS DA MÁQUINA (Manual Override - ATUALIZADO PARA NOVA ARQUITETURA)
# ============================================================================
@router.post("/sync-batch")
async def sync_offline_batch(payloads: List[dict], current_user: User = Depends(deps.get_current_active_user)):
    for item in payloads:
        process_sap_appointment.delay(appointment_data=item['payload'], organization_id=current_user.organization_id)
    return {"status": "batch_received", "count": len(payloads)}

@router.post("/machine/status")
async def set_machine_status(data: MachineStatusUpdate, db: AsyncSession = Depends(get_db)):
    """
    Define o status da máquina manualmente, respeitando a nova arquitetura explícita.
    """
    print(f"🔄 [BACKEND] Mudança Manual de Status: {data.status} -> Máquina {data.machine_id}")

    vehicle = await db.get(Vehicle, data.machine_id)
    if not vehicle: raise HTTPException(404, "Máquina não encontrada")
    
    status_upper = str(data.status).strip().upper()
    
    # --- MAPEAMENTO EXPLÍCITO ---
    new_status_db = "Disponível" 
    category_mes = "IDLE"

    # 1. SETUP
    if status_upper in ["SETUP", "PREPARAÇÃO"]:
        new_status_db = "Setup" # ✅ Novo status explícito
        category_mes = "PLANNED_STOP"

    # 2. MANUTENÇÃO
    elif status_upper in ["MAINTENANCE", "BROKEN", "MANUTENÇÃO", "QUEBRADA", "EM MANUTENÇÃO"]:
        new_status_db = "Em manutenção"
        category_mes = "MAINTENANCE"

    # 3. PRODUÇÃO AUTÔNOMA
    elif status_upper in ["IN_USE_AUTONOMOUS", "PRODUÇÃO AUTÔNOMA", "AUTÔNOMO"]:
        new_status_db = "Produção Autônoma" # ✅ Novo status explícito
        category_mes = "PRODUCING"

    # 4. PRODUÇÃO HUMANA
    elif status_upper in ["RUNNING", "IN_USE", "EM OPERAÇÃO", "EM USO"]:
        new_status_db = "Em uso"
        category_mes = "PRODUCING"

    # 5. OCIOSIDADE / PARADA
    elif status_upper in ["OCIOSO", "OCIOSIDADE"]:
        new_status_db = "Ociosidade" # ✅ Novo status explícito (Cinza)
        category_mes = "IDLE"
        
    elif status_upper in ["STOPPED", "PAUSED", "PARADA"]:
        new_status_db = "Parada"
        category_mes = "UNPLANNED_STOP"
        
    else:
        new_status_db = "Disponível"
        category_mes = "IDLE"

    print(f"✅ [BACKEND] Status Persistido: '{new_status_db}'")

    vehicle.status = new_status_db
    db.add(vehicle)
    
    try:
        await ProductionService.close_current_slice(db, vehicle.id)
        await ProductionService.open_new_slice(db, vehicle.id, category=category_mes, reason=f"Status: {new_status_db}")
    except Exception as e:
        print(f"⚠️ [BACKEND] Erro ao atualizar fatia MES: {e}")
    
    await db.commit()
    await db.refresh(vehicle)
    
    return {"message": "Status atualizado", "new_status": vehicle.status}

# ============================================================================
# 4. LISTAR MÁQUINAS
# ============================================================================
@router.get("/machines", response_model=List[vehicle_schema.VehiclePublic])
async def read_machines(db: AsyncSession = Depends(deps.get_db), skip: int = 0, limit: int = 100):
    query = select(Vehicle).offset(skip).limit(limit)
    machines = (await db.execute(query)).scalars().all()
    return machines

# ============================================================================
# 5. ANDON (ALERTAS)
# ============================================================================
@router.post("/andon")
async def open_andon_alert(alert: production_schema.AndonCreate, db: AsyncSession = Depends(deps.get_db)):
    machine = await db.get(Vehicle, alert.machine_id)
    if not machine: raise HTTPException(404, "Machine not found")

    query_op = select(User).where(or_(User.employee_id == alert.operator_badge, User.email == alert.operator_badge))
    operator = (await db.execute(query_op)).scalars().first()
    if not operator: raise HTTPException(404, "Operator not found")

    new_alert = AndonAlert(vehicle_id=machine.id, operator_id=operator.id, sector=alert.sector, notes=alert.notes, status="OPEN")
    db.add(new_alert)
    
    db.add(ProductionLog(
        vehicle_id=machine.id, 
        operator_id=operator.id,        # ID Numérico
        operator_badge=operator.employee_id, # Crachá String
        operator_name=operator.full_name,    # Nome String
        event_type="ANDON_OPEN", 
        details=f"Call: {alert.sector}", 
        timestamp=datetime.now()
    ))    
    await db.commit()
    return {"status": "success", "alert_id": new_alert.id}

# ============================================================================
# 6. REGISTRO DE EVENTOS (MES CORE)
# ============================================================================
@router.post("/event")
async def register_production_event(event: production_schema.ProductionEventCreate, db: AsyncSession = Depends(deps.get_db)):
    from app.core.websocket_manager import manager 
    try:
        # Se for Logout, apenas registramos o log e o estado, sem disparar lógica de apontamento SAP automática
        if event.event_type == "LOGOUT":
            print(f"ℹ️ [API] Logout detectado para Máquina {event.machine_id}. Pulando lógica de apontamento SAP redundante.")
            # Aqui você pode chamar uma versão simplificada ou apenas deixar o handle_event processar o banco
        
        result = await ProductionService.handle_event(db, event)
        
        await manager.broadcast({
            "type": "MACHINE_STATE_CHANGED",
            "machine_id": int(event.machine_id),
            "new_status": event.new_status,
            "category": result.get("category"),
            "machine_status_db": result.get("new_machine_status")
        })
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# 7. HISTÓRICO E OUTROS
# ============================================================================
@router.get("/stats/machine/{machine_id}/cards-summary")
async def get_machine_cards_summary(machine_id: int, days: int = 90, db: AsyncSession = Depends(deps.get_db)):
    start_date = datetime.now() - timedelta(days=days)
    stmt = (
        select(
            ProductionAppointment.op_number,
            func.sum(func.extract('epoch', ProductionAppointment.end_time - ProductionAppointment.start_time) / 3600).label('total_hours'),
            func.sum(ProductionAppointment.produced_qty).label('total_produced'),
            func.sum(ProductionAppointment.scrap_qty).label('total_scrap')
        )
        .where(
            ProductionAppointment.vehicle_id == machine_id,
            ProductionAppointment.start_time >= start_date,
            ProductionAppointment.appointment_type == "PRODUCTION"
        )
        .group_by(ProductionAppointment.op_number)
        .order_by(desc('total_hours'))
    )
    result = await db.execute(stmt)
    return [dict(row._mapping) for row in result.all()]

@router.get("/history/{machine_id}", response_model=List[production_schema.ProductionLogRead])
async def get_machine_history(machine_id: int, skip: int = 0, limit: int = 20, event_type: Optional[str] = None, db: AsyncSession = Depends(deps.get_db)):
    query = select(ProductionLog).where(ProductionLog.vehicle_id == machine_id)
    if event_type: query = query.where(ProductionLog.event_type == event_type)
    query = query.order_by(desc(ProductionLog.timestamp)).offset(skip).limit(limit)
    
    logs = (await db.execute(query)).scalars().all()
    history = []
    for log in logs:
        history.append({
            "id": log.id, 
            "event_type": log.event_type, 
            "timestamp": log.timestamp,
            "new_status": log.new_status, 
            "reason": log.reason, 
            "details": log.details,
            "operator_name": log.operator_name or "Sistema", # Usa o nome cacheado no log
            "operator_id": log.operator_id,                  # ID numérico para o link
            "operator_badge": log.operator_badge             # Crachá para exibir embaixo do nome
        })
    return history
# ============================================================================
# 8. SESSÕES (START/STOP)
# ============================================================================
@router.post("/session/start", response_model=SessionResponse)
async def start_session(payload: SessionStart, db: AsyncSession = Depends(deps.get_db)):
    op_code_str = str(payload.op_number)
    print(f"🚀 [MES] Iniciando OP {op_code_str} - Etapa {payload.step_seq}")
    
    machine = await db.get(Vehicle, payload.machine_id)
    if not machine: raise HTTPException(404, "Máquina não encontrada")

    user_q = await db.execute(select(User).where(or_(User.employee_id == payload.operator_badge, User.email == payload.operator_badge)))
    operator = user_q.scalars().first()
    if not operator: raise HTTPException(404, "Operador não encontrado")

    order_q = await db.execute(select(ProductionOrder).where(ProductionOrder.code == op_code_str))
    order = order_q.scalars().first()
    
    if not order:
        sap_service = SAPIntegrationService(db, organization_id=1)
        sap_op_data = await sap_service.get_production_order_by_code(op_code_str)
        part_name = "Item SAP"
        if sap_op_data:
            part_name = getattr(sap_op_data, 'part_name', sap_op_data.get('part_name', 'Item SAP'))

        order = ProductionOrder(code=op_code_str, part_name=part_name, status="SETUP", produced_quantity=0, scrap_quantity=0)
        db.add(order)
        await db.flush()

    active_session_q = await db.execute(select(ProductionSession).where(ProductionSession.vehicle_id == machine.id, ProductionSession.end_time == None))
    old_session = active_session_q.scalars().first()
    if old_session:
        old_session.end_time = datetime.now()
        db.add(old_session)

    new_session = ProductionSession(vehicle_id=machine.id, user_id=operator.id, production_order_id=order.id, start_time=datetime.now())
    db.add(new_session)
    await db.flush() 
    
    await ProductionService.open_new_slice(db, vehicle_id=machine.id, category="PLANNED_STOP", reason=f"Setup: {payload.step_seq}", session_id=new_session.id, order_id=order.id)
    
    machine.status = "Setup" 
    order.status = "SETUP"
    
    # ✅ CORREÇÃO AQUI
    log = ProductionLog(
        vehicle_id=machine.id, 
        
        # Usa o ID numérico do operador (que já foi buscado lá em cima)
        operator_id=operator.id, 
        
        # Salva o crachá e o nome para histórico
        operator_badge=str(payload.operator_badge),
        operator_name=operator.full_name,
        
        event_type="STATUS_CHANGE", 
        new_status="Setup",
        reason="Setup Inicial (Seleção de O.P.)",
        timestamp=datetime.now()
    )
    db.add(log)

    
    await db.commit()
    
    return {"status": "success", "message": f"Sessão iniciada: {payload.step_seq}", "session_id": str(new_session.id)}

@router.post("/session/stop")
async def stop_session(data: production_schema.SessionStopSchema, db: AsyncSession = Depends(deps.get_db)):
    q = select(ProductionSession).where(ProductionSession.vehicle_id == data.machine_id, ProductionSession.end_time == None)
    session = (await db.execute(q)).scalars().first()
    if not session: return {"status": "error", "message": "No active session"}

    end_time = datetime.now()
    await ProductionService.close_current_slice(db, data.machine_id, end_time)

    slices_q = select(ProductionTimeSlice).where(ProductionTimeSlice.session_id == session.id)
    slices = (await db.execute(slices_q)).scalars().all()
    
    total_prod = sum(s.duration_seconds for s in slices if s.category == 'PRODUCING')
    total_unprod = sum(s.duration_seconds for s in slices if s.category != 'PRODUCING')
    
    session.end_time = end_time
    session.duration_seconds = int((end_time - session.start_time).total_seconds())
    session.productive_seconds = int(total_prod)
    session.unproductive_seconds = int(total_unprod)
    
    machine = await db.get(Vehicle, session.vehicle_id)
    if machine.status != "Em manutenção": # Evita liberar se estiver quebrado
        machine.status = "Disponível"
        db.add(machine)

    db.add(session)
    await db.commit()
    return {"status": "success", "stats": {"total_time": session.duration_seconds, "productive": session.productive_seconds, "unproductive": session.unproductive_seconds}}

@router.get("/stats/machine/{machine_id}/oee")
async def get_machine_oee(machine_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None, db: AsyncSession = Depends(deps.get_db)):
    if not start_date: start_date = date.today()
    if not end_date: end_date = date.today()
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)
    return await ProductionService.calculate_oee(db, machine_id, dt_start, dt_end)

@router.get("/users/{user_id}/sessions", response_model=List[production_schema.SessionDetail])
async def get_user_sessions(user_id: int, start_date: date, end_date: date, db: AsyncSession = Depends(deps.get_db)):
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)
    query = select(ProductionSession).where(ProductionSession.user_id == user_id, ProductionSession.start_time >= dt_start, ProductionSession.start_time <= dt_end).order_by(desc(ProductionSession.start_time))
    sessions = (await db.execute(query)).scalars().all()
    session_details = []
    for sess in sessions:
        machine = await db.get(Vehicle, sess.vehicle_id)
        order_code = "---"
        if sess.production_order_id:
            order = await db.get(ProductionOrder, sess.production_order_id)
            if order: order_code = order.code
        total = sess.duration_seconds
        efficiency = (sess.productive_seconds / total * 100) if total > 0 else 0
        duration_str = f"{total // 3600}h {(total % 3600) // 60}m"
        session_details.append({
            "id": sess.id, "machine_name": f"{machine.brand} {machine.model}" if machine else "Desconhecida",
            "order_code": order_code, "start_time": sess.start_time, "end_time": sess.end_time,
            "duration": duration_str, "efficiency": round(efficiency, 1), "time_slices": []
        })
    return session_details

# ============================================================================
# 10. APONTAMENTO SAP E NOTIFICAÇÃO
# ============================================================================
async def notificar_quebra_maquina(op_number: str, machine_id: int, motivo: str, org_id: int):
    async with async_session() as db:
        try:
            machine = await db.get(Vehicle, machine_id)
            machine_name = f"{machine.brand} {machine.model}" if machine else f"Máquina {machine_id}"
            roles_alvo = [UserRole.MAINTENANCE, UserRole.PCP, UserRole.MANAGER, UserRole.ADMIN]
            query = select(User.device_token).where(User.organization_id == org_id, User.role.in_(roles_alvo), User.device_token.isnot(None))
            tokens = (await db.execute(query)).scalars().all()
            if tokens:
                linha_ordem = f"\nO.S.: {op_number}" if str(op_number).upper().startswith("OS-") else f"\nO.P.: {op_number}"
                if not op_number: linha_ordem = ""
                enviar_push_lista(tokens=list(tokens), title="🛑 MÁQUINA PARADA", body=f"{machine_name} parou.\nMotivo: {motivo}{linha_ordem}", data={"tipo": "manutencao", "machineId": str(machine_id)})
        except Exception as e: print(f"❌ Erro ao notificar quebra: {e}")

@router.post("/appoint")
async def create_appointment(data: ProductionAppointmentCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(deps.get_db), current_user: Optional[User] = Depends(deps.get_current_active_user)):
    sap_service = SAPIntegrationService(db, organization_id=1)
    appointment_dict = data.model_dump() if hasattr(data, 'model_dump') else data.dict()
    
    print(f"📡 [API] Enviando para SAP: OP {data.op_number}...")
    if not await sap_service.create_production_appointment(appointment_dict, sap_resource_code=data.resource_code):
        raise HTTPException(status_code=500, detail="Erro ao registrar no SAP")

    try:
        appt_type = "STOP" if data.stop_reason else "PRODUCTION"
        start_t = data.start_time.replace(tzinfo=None) if data.start_time else None
        end_t = data.end_time.replace(tzinfo=None) if data.end_time else None
        new_appointment = ProductionAppointment(
            op_number=data.op_number, operator_id=data.operator_id, vehicle_id=data.vehicle_id,
            start_time=start_t, end_time=end_t, position=data.position, operation_code=data.operation,
            appointment_type=appt_type, stop_reason=data.stop_reason, sap_status="SENT", sap_message="Sincronizado via /appoint"
        )
        db.add(new_appointment)
        await db.commit()
    except Exception as e: print(f"⚠️ [API] Erro ao salvar histórico local: {str(e)}")

    if data.stop_reason and str(data.stop_reason) in ['21', '34']:
        org_id = current_user.organization_id if current_user else 1
        background_tasks.add_task(notificar_quebra_maquina, op_number=data.op_number, machine_id=data.vehicle_id, motivo=f"Manutenção (Cód {data.stop_reason})", org_id=org_id)

    return {"message": "Apontamento realizado e salvo!"}

@router.get("/orders/open", response_model=List[ProductionOrderRead])
async def get_open_orders(db: AsyncSession = Depends(deps.get_db)):
    sap_service = SAPIntegrationService(db, organization_id=1)
    ops = await sap_service.get_released_production_orders()
    oss = await sap_service.get_open_service_orders()
    return ops + oss

@router.get("/orders/{code}", response_model=production_schema.ProductionOrderRead)
async def get_production_order(code: str, db: AsyncSession = Depends(deps.get_db)):
    sap_service = SAPIntegrationService(db, organization_id=1)
    sap_data = await sap_service.get_production_order_by_code(code)
    if sap_data: return sap_data
    raise HTTPException(status_code=404, detail="Ordem não encontrada no SAP (O.P. ou O.S.)")

@router.get("/history/user/{user_id}")
async def get_user_production_history(user_id: int, db: AsyncSession = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    user = await db.get(User, user_id)
    if not user or not user.employee_id: return []
    badge = str(user.employee_id)
    stmt = select(ProductionAppointment, Vehicle).outerjoin(Vehicle, ProductionAppointment.vehicle_id == Vehicle.id).where(and_(ProductionAppointment.operator_id == badge, ProductionAppointment.appointment_type == "PRODUCTION")).order_by(desc(ProductionAppointment.start_time)).limit(2000)
    result = await db.execute(stmt)
    history = []
    for appointment, vehicle in result.all():
        duration_min = int((appointment.end_time - appointment.start_time).total_seconds() / 60) if appointment.start_time and appointment.end_time else 0
        efficiency = int((appointment.produced_qty / appointment.target_qty) * 100) if appointment.target_qty and appointment.target_qty > 0 else 100
        if efficiency > 150: efficiency = 150
        history.append({
            "id": appointment.id, "machine_name": f"{vehicle.brand} {vehicle.model}" if vehicle else f"Máquina #{appointment.vehicle_id}",
            "op_number": appointment.op_number or "N/A", "step": appointment.position or "",
            "start_time": appointment.start_time.isoformat() if appointment.start_time else None,
            "end_time": appointment.end_time.isoformat() if appointment.end_time else None,
            "duration_minutes": duration_min, "efficiency": efficiency
        })
    return history