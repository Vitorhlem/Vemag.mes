from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, date, time, timedelta
from typing import List, Optional
from pydantic import BaseModel

# Imports do Projeto
from app.db.session import get_db
from app import deps
from app.models.production_model import ProductionOrder, ProductionSession, ProductionLog, AndonAlert, ProductionTimeSlice
from app.models.user_model import User
from app.services.production_service import ProductionService
from app.services.sap_sync import SAPIntegrationService
from app.schemas import production_schema, vehicle_schema, user_schema
from app.schemas.production_schema import ProductionAppointmentCreate, ProductionOrderRead, MachineDailyStats

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

# ============================================================================
# 1. ESTATÍSTICAS DA MÁQUINA (CORRIGIDO ASYNC)
# ============================================================================
@router.get("/stats/{machine_id}", response_model=MachineDailyStats)
async def get_machine_stats(
    machine_id: int,
    target_date: date = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Calcula o tempo gasto em cada estado da máquina no dia especificado.
    Analisa a linha do tempo de eventos (Logs).
    """
    if not target_date:
        target_date = date.today()

    # Define o intervalo do dia
    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)
    
    if target_date == date.today():
        end_of_day = datetime.now()

    # 1. Buscar último log ANTES do dia começar (para estado inicial)
    # Nota: Usamos vehicle_id pois é o nome da coluna no banco
    stmt_last = select(ProductionLog).filter(
        ProductionLog.vehicle_id == machine_id,
        ProductionLog.timestamp < start_of_day
    ).order_by(ProductionLog.timestamp.desc()).limit(1)
    
    result_last = await db.execute(stmt_last)
    last_log_before = result_last.scalars().first()

    # 2. Buscar logs DO DIA
    stmt_logs = select(ProductionLog).filter(
        ProductionLog.vehicle_id == machine_id,
        ProductionLog.timestamp >= start_of_day,
        ProductionLog.timestamp <= end_of_day
    ).order_by(ProductionLog.timestamp.asc())

    result_logs = await db.execute(stmt_logs)
    todays_logs = result_logs.scalars().all()

    # --- LÓGICA DE CÁLCULO ---
    current_status = last_log_before.new_status if last_log_before else "IDLE"
    is_operator_present = (last_log_before.event_type == 'LOGIN') if last_log_before else False
    
    stats = {
        "running_op": 0.0,
        "running_auto": 0.0,
        "paused_op": 0.0,
        "maintenance": 0.0,
        "idle": 0.0
    }

    timeline = []
    timeline.append({
        "time": start_of_day, 
        "status": current_status, 
        "has_op": is_operator_present
    })

    for log in todays_logs:
        if log.event_type == 'LOGIN':
            is_operator_present = True
        elif log.event_type == 'LOGOUT':
            is_operator_present = False
        
        if log.new_status:
            current_status = log.new_status

        timeline.append({
            "time": log.timestamp,
            "status": current_status,
            "has_op": is_operator_present
        })

    timeline.append({"time": end_of_day, "status": "IGNORE", "has_op": False})

    for i in range(len(timeline) - 1):
        segment_start = timeline[i]
        segment_end = timeline[i+1]
        
        duration = (segment_end["time"] - segment_start["time"]).total_seconds()
        
        st = str(segment_start["status"]).upper()
        op = segment_start["has_op"]

        if "MAINTENANCE" in st or "MANUTENÇÃO" in st or "MANUTENCAO" in st:
            stats["maintenance"] += duration
        
        elif "RUNNING" in st or "EM OPERAÇÃO" in st or "EM USO" in st:
            if op:
                stats["running_op"] += duration
            else:
                stats["running_auto"] += duration
        
        elif ("PAUSED" in st or "PARADA" in st or "STOPPED" in st):
            if op:
                stats["paused_op"] += duration
            else:
                stats["idle"] += duration 
        
        else:
            stats["idle"] += duration

    def fmt(seconds):
        return str(timedelta(seconds=int(seconds)))

    return MachineDailyStats(
        date=str(target_date),
        total_running_operator_seconds=stats["running_op"],
        total_running_autonomous_seconds=stats["running_auto"],
        total_paused_operator_seconds=stats["paused_op"],
        total_maintenance_seconds=stats["maintenance"],
        total_idle_seconds=stats["idle"],
        formatted_running_operator=fmt(stats["running_op"]),
        formatted_running_autonomous=fmt(stats["running_auto"]),
        formatted_paused_operator=fmt(stats["paused_op"]),
        formatted_maintenance=fmt(stats["maintenance"])
    )

# ============================================================================
# 2. OPERADOR (Busca por Crachá)
# ============================================================================
@router.get("/operator/{badge}", response_model=user_schema.UserPublic)
async def get_operator_by_badge(
    badge: str, 
    db: AsyncSession = Depends(deps.get_db)
):
    print(f"🔍 [DEBUG KIOSK] Buscando Operador. Badge recebido: '{badge}'")
    
    clean_badge = badge.strip()
    
    # 1. Tenta por Matrícula
    loader_opt = selectinload(User.organization)
    query = select(User).options(loader_opt).where(User.employee_id == clean_badge)
    result = await db.execute(query)
    user = result.scalars().first()
    
    if user:
        print(f"✅ [DEBUG KIOSK] Encontrado por Matrícula: {user.full_name} (ID: {user.employee_id})")
    
    # 2. Tenta por Email
    if not user:
        query = select(User).options(loader_opt).where(func.lower(User.email) == clean_badge.lower())
        result = await db.execute(query)
        user = result.scalars().first()
        if user:
            print(f"✅ [DEBUG KIOSK] Encontrado por Email: {user.full_name}")

    if not user:
        print(f"❌ [DEBUG KIOSK] Operador não encontrado para: {clean_badge}")
        raise HTTPException(status_code=404, detail="Operador não encontrado.")
        
    return user

# ============================================================================
# 3. STATUS DA MÁQUINA (Manual Override)
# ============================================================================
@router.post("/machine/status")
async def set_machine_status(
    data: MachineStatusUpdate, 
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Força uma mudança de status manual.
    IMPORTANTE: Isso também deve fechar a fatia de tempo atual para manter a consistência do MES.
    """
    query = select(Vehicle).where(Vehicle.id == data.machine_id)
    result = await db.execute(query)
    vehicle = result.scalars().first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    # Mapeamento e Lógica de Enum
    status_upper = data.status.upper()
    new_status_enum = VehicleStatus.AVAILABLE
    
    category_mes = "IDLE" # Default

    if status_upper in ["MAINTENANCE", "BROKEN", "SETUP", "MANUTENÇÃO"]:
        new_status_enum = VehicleStatus.MAINTENANCE
        category_mes = "PLANNED_STOP"
    elif status_upper in ["RUNNING", "IN_USE", "EM USO", "EM OPERAÇÃO"]:
        new_status_enum = VehicleStatus.IN_USE
        category_mes = "PRODUCING"
    
    # 1. Atualiza Veículo
    vehicle.status = new_status_enum.value
    db.add(vehicle)
    
    # 2. MES: Fecha fatia anterior e abre nova (Genérica)
    await ProductionService.close_current_slice(db, vehicle.id)
    await ProductionService.open_new_slice(db, vehicle.id, category=category_mes, reason="Manual Override")
    
    await db.commit()
    return {"message": "Status atualizado", "new_status": vehicle.status}

# ============================================================================
# 4. LISTAR MÁQUINAS
# ============================================================================
@router.get("/machines", response_model=List[vehicle_schema.VehiclePublic])
async def read_machines(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
):
    query = select(Vehicle).offset(skip).limit(limit)
    result = await db.execute(query)
    machines = result.scalars().all()
    return machines

# ============================================================================
# 5. ANDON (ALERTAS)
# ============================================================================
@router.post("/andon")
async def open_andon_alert(
    alert: production_schema.AndonCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    machine = await db.get(Vehicle, alert.machine_id)
    if not machine: raise HTTPException(404, "Machine not found")

    # Busca flexível (Matrícula ou Email)
    query_op = select(User).where(or_(
        User.employee_id == alert.operator_badge,
        User.email == alert.operator_badge
    ))
    result_op = await db.execute(query_op)
    operator = result_op.scalars().first()
    
    if not operator: raise HTTPException(404, "Operator not found")

    new_alert = AndonAlert(
        vehicle_id=machine.id,
        operator_id=operator.id,
        sector=alert.sector,
        notes=alert.notes,
        status="OPEN"
    )
    db.add(new_alert)
    
    log = ProductionLog(
        vehicle_id=machine.id, 
        operator_id=operator.id,
        event_type="ANDON_OPEN",
        details=f"Call for: {alert.sector}",
        timestamp=datetime.now()
    )
    db.add(log)
    
    await db.commit()
    return {"status": "success", "alert_id": new_alert.id}

# ============================================================================
# 6. REGISTRO DE EVENTOS (MES CORE)
# ============================================================================
@router.post("/event")
async def register_production_event(
    event: production_schema.ProductionEventCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Endpoint Central do Cockpit.
    Delega toda a lógica para o ProductionService.
    """
    try:
        result = await ProductionService.handle_event(db, event)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[ERRO CRÍTICO] Event Handler: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ============================================================================
# 7. HISTÓRICO
# ============================================================================
@router.get("/history/{machine_id}", response_model=List[production_schema.ProductionLogRead])
async def get_machine_history(
    machine_id: int,
    skip: int = 0,
    limit: int = 20,
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db)
):
    # Uso de vehicle_id
    query = select(ProductionLog).where(ProductionLog.vehicle_id == machine_id)
    if event_type:
        query = query.where(ProductionLog.event_type == event_type)
    query = query.order_by(desc(ProductionLog.timestamp)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Join manual para pegar nome do operador
    history = []
    for log in logs:
        op_name = "System"
        if log.operator_id:
            op = await db.get(User, log.operator_id)
            if op: op_name = op.full_name or op.email
            
        history.append({
            "id": log.id,
            "event_type": log.event_type,
            "timestamp": log.timestamp,
            "new_status": log.new_status,
            "reason": log.reason,
            "details": log.details,
            "operator_name": op_name
        })
        
    return history

# ============================================================================
# 8. SESSÕES (START/STOP) COM INTEGRAÇÃO MES
# ============================================================================
@router.post("/session/start")
async def start_session(
    data: production_schema.SessionStartSchema,
    db: AsyncSession = Depends(deps.get_db)
):
    print(f"🚀 [DEBUG KIOSK] Iniciando Sessão. Badge: '{data.operator_badge}'") 
    machine = await db.get(Vehicle, data.machine_id)
    if not machine: raise HTTPException(404, "Invalid Machine")

    res = await db.execute(select(User).where(or_(
        User.employee_id == data.operator_badge,
        User.email == data.operator_badge
    )))
    operator = res.scalars().first()
    if operator:
        print(f"👤 [DEBUG KIOSK] Usuário: {operator.full_name}")
    else:
        print(f"❌ [DEBUG KIOSK] Usuário não encontrado!")
        raise HTTPException(404, "Invalid Badge")

    res_ord = await db.execute(select(ProductionOrder).where(ProductionOrder.code == data.order_code))
    order = res_ord.scalars().first()
    if not order: raise HTTPException(404, "P.O. not found")

    # 1. Encerra sessão anterior (Segurança)
    active_session_q = await db.execute(select(ProductionSession).where(
        ProductionSession.vehicle_id == machine.id,
        ProductionSession.end_time == None
    ))
    old_session = active_session_q.scalars().first()
    if old_session:
        await ProductionService.close_current_slice(db, machine.id)
        old_session.end_time = datetime.now()
        db.add(old_session)

    # 2. Cria Nova Sessão
    new_session = ProductionSession(
        vehicle_id=machine.id,
        user_id=operator.id,
        production_order_id=order.id,
        start_time=datetime.now()
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # 3. MES: Abre primeira fatia como SETUP
    await ProductionService.open_new_slice(
        db, 
        vehicle_id=machine.id, 
        category="PLANNED_STOP", 
        reason="Setup Inicial de Sessão", 
        session_id=new_session.id,
        order_id=order.id
    )
    
    # 4. Atualiza Status Visual
    machine.status = VehicleStatus.MAINTENANCE.value
    order.status = "SETUP"
    db.add(machine)
    db.add(order)

    await db.commit()
    return {"status": "success", "session_id": new_session.id}


@router.post("/session/stop")
async def stop_session(
    data: production_schema.SessionStopSchema,
    db: AsyncSession = Depends(deps.get_db)
):
    # 1. Busca sessão ativa
    q = select(ProductionSession).where(
        ProductionSession.vehicle_id == data.machine_id,
        ProductionSession.end_time == None
    )
    res = await db.execute(q)
    session = res.scalars().first()
    
    if not session:
        return {"status": "error", "message": "No active session"}

    end_time = datetime.now()
    
    # 2. MES: Fecha última fatia
    await ProductionService.close_current_slice(db, data.machine_id, end_time)

    # 3. CÁLCULO PRECISO (Soma Time Slices)
    slices_q = select(ProductionTimeSlice).where(
        ProductionTimeSlice.session_id == session.id
    )
    slices_res = await db.execute(slices_q)
    slices = slices_res.scalars().all()
    
    total_prod = sum(s.duration_seconds for s in slices if s.category == 'PRODUCING')
    total_unprod = sum(s.duration_seconds for s in slices if s.category != 'PRODUCING')
    
    # Atualiza Sessão
    session.end_time = end_time
    session.duration_seconds = int((end_time - session.start_time).total_seconds())
    session.productive_seconds = int(total_prod)
    session.unproductive_seconds = int(total_unprod)
    
    # 4. Libera Máquina (Se não estiver quebrada)
    machine = await db.get(Vehicle, session.vehicle_id)
    if machine.status != VehicleStatus.MAINTENANCE.value:
        machine.status = VehicleStatus.AVAILABLE.value
        db.add(machine)

    db.add(session)
    await db.commit()
    
    return {
        "status": "success", 
        "stats": {
            "total_time": session.duration_seconds,
            "productive": session.productive_seconds,
            "unproductive": session.unproductive_seconds
        }
    }

# ============================================================================
# 9. RELATÓRIOS & OEE
# ============================================================================

@router.get("/stats/machine/{machine_id}/oee")
async def get_machine_oee(
    machine_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(deps.get_db)
):
    if not start_date: start_date = date.today()
    if not end_date: end_date = date.today()
    
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)
    
    metrics = await ProductionService.calculate_oee(db, machine_id, dt_start, dt_end)
    return metrics

@router.get("/stats/employees", response_model=List[production_schema.EmployeeStatsRead])
async def get_employee_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    if not start_date: start_date = date.today().replace(day=1)
    if not end_date: end_date = date.today()
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)

    query_users = select(User).where(User.organization_id == current_user.organization_id)
    users = (await db.execute(query_users)).scalars().all()
    
    stats_list = []

    for user in users:
        q_sess = select(ProductionSession).where(
            ProductionSession.user_id == user.id,
            ProductionSession.start_time >= dt_start,
            ProductionSession.start_time <= dt_end
        )
        sessions = (await db.execute(q_sess)).scalars().all()

        total_sec = sum(s.duration_seconds for s in sessions)
        prod_sec = sum(s.productive_seconds for s in sessions)
        unprod_sec = sum(s.unproductive_seconds for s in sessions)
        
        efficiency = (prod_sec / total_sec * 100) if total_sec > 0 else 0

        stats_list.append({
            "id": user.id, 
            "employee_name": user.full_name or user.email,
            "total_hours": round(total_sec / 3600, 2),
            "productive_hours": round(prod_sec / 3600, 2),
            "unproductive_hours": round(unprod_sec / 3600, 2),
            "efficiency": round(efficiency, 1),
            "top_reasons": [] 
        })
    
    stats_list.sort(key=lambda x: x['total_hours'], reverse=True)
    return stats_list

@router.get("/users/{user_id}/sessions", response_model=List[production_schema.SessionDetail])
async def get_user_sessions(
    user_id: int,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(deps.get_db)
):
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)

    query = select(ProductionSession).where(
        ProductionSession.user_id == user_id,
        ProductionSession.start_time >= dt_start,
        ProductionSession.start_time <= dt_end
    ).order_by(desc(ProductionSession.start_time))

    result = await db.execute(query)
    sessions = result.scalars().all()
    
    session_details = []
    
    for sess in sessions:
        machine = await db.get(Vehicle, sess.vehicle_id)
        
        order_code = "---"
        if sess.production_order_id:
            order = await db.get(ProductionOrder, sess.production_order_id)
            if order: order_code = order.code
            
        total = sess.duration_seconds
        prod = sess.productive_seconds
        efficiency = (prod / total * 100) if total > 0 else 0
        
        hours = total // 3600
        mins = (total % 3600) // 60
        duration_str = f"{hours}h {mins}m" if hours > 0 else f"{mins} min"
        
        session_details.append({
            "id": sess.id,
            "machine_name": f"{machine.brand} {machine.model}" if machine else "Desconhecida",
            "order_code": order_code,
            "start_time": sess.start_time,
            "end_time": sess.end_time,
            "duration": duration_str,
            "efficiency": round(efficiency, 1),
            "time_slices": []
        })
        
    return session_details

# ============================================================================
# 10. APONTAMENTO SAP
# ============================================================================
@router.post("/appoint")
async def create_appointment(
    data: ProductionAppointmentCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    resource_code = data.resource_code
    sap_employee_id = data.operator_id
    if "@" in sap_employee_id:
        print(f"⚠️ AVISO: Recebido email no operador ({sap_employee_id}).") 
        
    sap_service = SAPIntegrationService(db, organization_id=1)
    
    try:
        appointment_dict = data.model_dump()
    except AttributeError:
        appointment_dict = data.dict()
    
    success = await sap_service.create_production_appointment(
        appointment_dict, 
        sap_resource_code=resource_code
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao registrar no SAP")
    
    return {"message": "Apontamento realizado!"}

# ============================================================================
# 11. OPs DO SAP
# ============================================================================
@router.get("/orders/open", response_model=List[ProductionOrderRead])
async def get_open_orders(
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Retorna a lista de OPs liberadas direto do SAP.
    """
    sap_service = SAPIntegrationService(db, organization_id=1)
    orders = await sap_service.get_released_production_orders()
    return orders

@router.get("/orders/{code}", response_model=production_schema.ProductionOrderRead)
async def get_production_order(
    code: str, 
    db: AsyncSession = Depends(deps.get_db)
):
    print(f"🔎 Buscando OP {code} no SAP...")
    sap_service = SAPIntegrationService(db, organization_id=1)
    sap_data = await sap_service.get_production_order_by_code(code)
    
    if sap_data:
        return sap_data
        
    raise HTTPException(status_code=404, detail="OP não encontrada no SAP")