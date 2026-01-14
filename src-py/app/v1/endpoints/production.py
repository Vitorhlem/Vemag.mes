from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, date, time
from typing import List, Optional
from pydantic import BaseModel

# Imports do Projeto
from app import deps 
from app.schemas import production_schema, vehicle_schema
from app.models.production_model import ProductionLog, ProductionOrder, AndonAlert, ProductionSession
from app.models.user_model import User

# --- IMPORT DO MODELO COM ENUM ---
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
# 1. ROTA DE STATUS DA MÁQUINA
# ============================================================================
@router.post("/machine/status")
async def set_machine_status(
    data: MachineStatusUpdate, 
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Recebe status em INGLÊS (ex: 'MAINTENANCE') e salva o valor do ENUM (ex: 'Em manutenção').
    """
    query = select(Vehicle).where(Vehicle.id == data.machine_id)
    result = await db.execute(query)
    vehicle = result.scalars().first()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    # TRADUÇÃO: API (Inglês) -> BANCO (Português do Enum)
    status_upper = data.status.upper()
    new_status = data.status # Fallback padrão

    # Mapeamento Estrito
    if status_upper in ["MAINTENANCE", "BROKEN", "SETUP"]:
        new_status = VehicleStatus.MAINTENANCE.value # Salva: "Em manutenção"
    elif status_upper in ["AVAILABLE", "IDLE", "STOPPED", "OFFLINE"]:
        new_status = VehicleStatus.AVAILABLE.value   # Salva: "Disponível"
    elif status_upper in ["RUNNING", "IN_USE"]:
        new_status = VehicleStatus.IN_USE.value      # Salva: "Em uso"

    print(f"[DEBUG] set_machine_status: Recebido '{data.status}' -> Convertido para '{new_status}'")
    
    vehicle.status = new_status
    db.add(vehicle)
    
    try:
        await db.commit()
        await db.refresh(vehicle)
    except Exception as e:
        await db.rollback()
        print(f"[ERRO] {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar status")
    
    return {"message": "Status atualizado", "new_status": vehicle.status}

# ============================================================================
# 2. LISTAR MÁQUINAS
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
# 3. ANDON (ALERTAS)
# ============================================================================
@router.post("/andon")
async def open_andon_alert(
    alert: production_schema.AndonCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    machine = await db.get(Vehicle, alert.machine_id)
    if not machine: raise HTTPException(404, "Machine not found")

    query_op = select(User).where(User.email == alert.operator_badge)
    result_op = await db.execute(query_op)
    operator = result_op.scalars().first()
    
    if not operator and alert.operator_badge == "BADGE-123":
        res = await db.execute(select(User).limit(1))
        operator = res.scalars().first()
    
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
# 4. REGISTRO DE EVENTOS (LOGOUT / PARADAS)
# ============================================================================
@router.post("/event")
async def register_production_event(
    event: production_schema.ProductionEventCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    # A. Validar Máquina
    machine = await db.get(Vehicle, event.machine_id)
    if not machine: raise HTTPException(404, "Machine not found")

    # B. Validar Operador (CORRIGIDO: result_op)
    query_op = select(User).where(User.email == event.operator_badge)
    result_op = await db.execute(query_op) 
    operator = result_op.scalars().first()
    
    if not operator and event.operator_badge == "BADGE-123":
        res = await db.execute(select(User).limit(1))
        operator = res.scalars().first()
    if not operator: raise HTTPException(404, "Operator not found")

    # C. Processar O.P.
    order = None
    if event.order_code:
        res_ord = await db.execute(select(ProductionOrder).where(ProductionOrder.code == event.order_code))
        order = res_ord.scalars().first()
        if order:
            if event.event_type == 'COUNT':
                order.produced_quantity += (event.quantity_good or 0)
                order.scrap_quantity += (event.quantity_scrap or 0)
                db.add(order)
            if event.new_status == 'RUNNING': order.status = 'RUNNING'
            elif event.new_status == 'STOPPED': order.status = 'PAUSED'
            db.add(order)

    # D. Atualizar Status da Máquina (Com Blindagem e Tradução)
    if event.new_status:
        print(f"\n[DEBUG] Event: {event.event_type} | Solicitado: '{event.new_status}'")
        
        # Mapa: API (Inglês) -> Enum Real (Português)
        status_map = {
            "RUNNING":      VehicleStatus.IN_USE.value,
            "SETUP":        VehicleStatus.MAINTENANCE.value,
            "STOPPED":      VehicleStatus.AVAILABLE.value,
            "IDLE":         VehicleStatus.AVAILABLE.value,
            "AVAILABLE":    VehicleStatus.AVAILABLE.value,
            "OFFLINE":      VehicleStatus.AVAILABLE.value,
            "MAINTENANCE":  VehicleStatus.MAINTENANCE.value,
            "BROKEN":       VehicleStatus.MAINTENANCE.value
        }
        
        target_db_status = status_map.get(event.new_status)
        current_db_status = str(machine.status) 

        # LÓGICA DE BLINDAGEM:
        # Se a máquina já está "Em manutenção" e o evento tenta mudar para "Disponível" (ex: Logout), BLOQUEIA.
        is_broken = current_db_status == VehicleStatus.MAINTENANCE.value
        is_trying_to_free = target_db_status == VehicleStatus.AVAILABLE.value

        if is_broken and is_trying_to_free:
            print(f"[DEBUG] 🛡️ BLOQUEADO: Máquina está '{current_db_status}'. Ignorando mudança para '{target_db_status}'.")
        elif target_db_status:
            machine.status = target_db_status 
            db.add(machine)
            print(f"[DEBUG] Status alterado para: '{machine.status}'")

    # E. Log
    log_entry = ProductionLog(
        vehicle_id=machine.id,
        operator_id=operator.id,
        order_id=order.id if order else None,
        event_type=event.event_type,
        reason=event.reason,
        details=event.details,
        new_status=event.new_status,
        previous_status=machine.status,
        timestamp=datetime.now()
    )
    db.add(log_entry)
    
    await db.commit()
    return {"status": "success"}

# ============================================================================
# 5. HISTÓRICO E P.O.
# ============================================================================
@router.get("/history/{machine_id}", response_model=List[production_schema.ProductionLogRead])
async def get_machine_history(
    machine_id: int,
    skip: int = 0,
    limit: int = 20,
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db)
):
    query = select(ProductionLog).where(ProductionLog.vehicle_id == machine_id)
    if event_type:
        query = query.where(ProductionLog.event_type == event_type)
    query = query.order_by(desc(ProductionLog.timestamp)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
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

@router.get("/orders/{code}", response_model=production_schema.ProductionOrder)
async def get_production_order(code: str, db: AsyncSession = Depends(deps.get_db)):
    query = select(ProductionOrder).where(ProductionOrder.code == code)
    result = await db.execute(query)
    order = result.scalars().first()
    
    if not order:
        order = ProductionOrder(
            code=code,
            part_name="OS-12391-20",
            target_quantity=500,
            produced_quantity=0,
            scrap_quantity=0,
            status="PENDING",
            part_image_url=""
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
    return order

# ============================================================================
# 6. SESSÕES (START/STOP)
# ============================================================================
@router.post("/session/start")
async def start_session(
    data: production_schema.SessionStartSchema,
    db: AsyncSession = Depends(deps.get_db)
):
    machine = await db.get(Vehicle, data.machine_id)
    if not machine: raise HTTPException(404, "Invalid Machine")

    res = await db.execute(select(User).where(User.email == data.operator_badge))
    operator = res.scalars().first()
    if not operator: 
        if data.operator_badge == "BADGE-123":
            res = await db.execute(select(User).limit(1))
            operator = res.scalars().first()
        if not operator: raise HTTPException(404, "Invalid Badge")

    res_ord = await db.execute(select(ProductionOrder).where(ProductionOrder.code == data.order_code))
    order = res_ord.scalars().first()
    if not order: raise HTTPException(404, "P.O. not found")

    # Close previous
    active_session_q = await db.execute(select(ProductionSession).where(
        ProductionSession.vehicle_id == machine.id,
        ProductionSession.end_time == None
    ))
    old_session = active_session_q.scalars().first()
    if old_session:
        old_session.end_time = datetime.now()
        db.add(old_session)

    # New Session
    new_session = ProductionSession(
        vehicle_id=machine.id,
        user_id=operator.id,
        production_order_id=order.id,
        start_time=datetime.now()
    )
    db.add(new_session)
    
    # Inicio de Sessão = Manutenção/Setup (No Enum correto)
    machine.status = VehicleStatus.MAINTENANCE.value 
    db.add(machine)
    
    order.status = "SETUP"
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

    # 2. Define fim
    end_time = datetime.now()
    session.end_time = end_time

    # 3. Cálculos de Tempo
    logs_q = select(ProductionLog).where(
        ProductionLog.vehicle_id == data.machine_id,
        ProductionLog.timestamp >= session.start_time
    ).order_by(ProductionLog.timestamp)
    
    logs_res = await db.execute(logs_q)
    logs = logs_res.scalars().all()

    total_prod = 0.0
    total_unprod = 0.0
    cursor_time = session.start_time
    current_status = "SETUP" 

    virtual_logs = list(logs)
    virtual_logs.append(ProductionLog(timestamp=end_time, new_status="SESSION_END"))

    for log in virtual_logs:
        delta = (log.timestamp - cursor_time).total_seconds()
        if delta > 0:
            if current_status == "RUNNING" or current_status == "IN_USE":
                total_prod += delta
            else:
                if delta <= 300: 
                    total_prod += delta
                else:
                    total_unprod += delta
        cursor_time = log.timestamp
        if log.new_status != "SESSION_END":
            current_status = log.new_status or current_status

    session.duration_seconds = int((end_time - session.start_time).total_seconds())
    session.productive_seconds = int(total_prod)
    session.unproductive_seconds = int(total_unprod)

    # --- BLINDAGEM NO STOP ---
    machine = await db.get(Vehicle, session.vehicle_id)
    
    current_status = str(machine.status)
    print(f"[DEBUG] Stop Session. Status Atual no Banco: '{current_status}'")

    # Verifica se é "Em manutenção"
    if current_status == VehicleStatus.MAINTENANCE.value:
        print("[DEBUG] Sessão encerrada, mas máquina quebrada. Mantendo 'Em manutenção'.")
    else:
        print("[DEBUG] Sessão encerrada. Liberando para 'Disponível'.")
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
# 7. RELATÓRIOS
# ============================================================================
@router.get("/stats/employees", response_model=List[production_schema.EmployeeStatsRead])
async def get_employee_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(deps.get_db)
):
    if not start_date: start_date = date.today().replace(day=1)
    if not end_date: end_date = date.today()
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)

    users = (await db.execute(select(User))).scalars().all()
    stats_list = []

    for user in users:
        query = select(ProductionSession).where(
            ProductionSession.user_id == user.id,
            ProductionSession.start_time <= dt_end,
            (ProductionSession.end_time >= dt_start) | (ProductionSession.end_time == None)
        )
        sessions = (await db.execute(query)).scalars().all()

        if not sessions:
            stats_list.append({
                "employee_name": user.full_name or user.email,
                "total_hours": 0, "productive_hours": 0, "unproductive_hours": 0,
                "efficiency": 0, "top_reasons": []
            })
            continue

        total_sec = sum(s.duration_seconds for s in sessions)
        prod_sec = sum(s.productive_seconds for s in sessions)
        unprod_sec = sum(s.unproductive_seconds for s in sessions)
        
        now = datetime.now()
        for s in sessions:
            if s.end_time is None:
                current_duration = (now - s.start_time).total_seconds()
                total_sec += current_duration

        efficiency = (prod_sec / total_sec * 100) if total_sec > 0 else 0

        reason_q = select(
            ProductionLog.reason, 
            func.count(ProductionLog.id).label('count')
        ).join(ProductionSession).where(
            ProductionSession.user_id == user.id,
            ProductionLog.new_status.in_(['STOPPED', 'MAINTENANCE', 'SETUP']),
            ProductionLog.timestamp.between(dt_start, dt_end)
        ).group_by(ProductionLog.reason).order_by(desc('count')).limit(3)
        
        reasons_res = (await db.execute(reason_q)).all()
        top_reasons = [{"label": r.reason or "Não Inf.", "count": r.count} for r in reasons_res]

        stats_list.append({
            "employee_name": user.full_name or user.email,
            "total_hours": round(total_sec / 3600, 2),
            "productive_hours": round(prod_sec / 3600, 2),
            "unproductive_hours": round(unprod_sec / 3600, 2),
            "efficiency": round(efficiency, 1),
            "top_reasons": top_reasons
        })
    
    stats_list.sort(key=lambda x: x['total_hours'], reverse=True)
    return stats_list

@router.get("/stats/employee/{user_id}/details", response_model=production_schema.EmployeeDetailRead)
async def get_employee_details(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(deps.get_db)
):
    if not start_date: start_date = date.today().replace(day=1)
    if not end_date: end_date = date.today()
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)

    q_sessions = select(ProductionSession).where(
        ProductionSession.user_id == user_id,
        ProductionSession.start_time.between(dt_start, dt_end)
    ).order_by(desc(ProductionSession.start_time))
    
    sessions = (await db.execute(q_sessions)).scalars().all()

    total_sec = 0.0
    prod_sec = 0.0
    unprod_sec = 0.0
    session_details = []
    
    for s in sessions:
        machine = await db.get(Vehicle, s.vehicle_id)
        order = await db.get(ProductionOrder, s.production_order_id) if s.production_order_id else None
        
        dur = s.duration_seconds
        prod = s.productive_seconds
        unprod = s.unproductive_seconds
        
        if s.end_time is None:
            dur = (datetime.now() - s.start_time).total_seconds()
        
        total_sec += dur
        prod_sec += prod
        unprod_sec += unprod
        
        eff = (prod / dur * 100) if dur > 0 else 0
        
        m, sec = divmod(dur, 60)
        h, m = divmod(m, 60)
        dur_str = f"{int(h):02d}:{int(m):02d}:{int(sec):02d}"

        session_details.append({
            "id": s.id,
            "machine_name": f"{machine.brand} {machine.model}" if machine else "Máquina Desc.",
            "order_code": order.code if order else "N/A",
            "start_time": s.start_time,
            "end_time": s.end_time,
            "duration": dur_str,
            "efficiency": round(eff, 1)
        })

    q_reasons = select(
        ProductionLog.reason,
        func.count(ProductionLog.id).label('count')
    ).where(
        ProductionLog.operator_id == user_id,
        ProductionLog.timestamp.between(dt_start, dt_end),
        ProductionLog.new_status.in_(['STOPPED', 'MAINTENANCE', 'SETUP'])
    ).group_by(ProductionLog.reason).order_by(desc('count'))
    
    reasons_res = (await db.execute(q_reasons)).all()
    
    top_reasons = []
    for r in reasons_res:
        if r.reason:
            top_reasons.append({
                "label": r.reason,
                "count": r.count,
                "duration_minutes": 0 
            })

    total_eff = (prod_sec / total_sec * 100) if total_sec > 0 else 0

    return {
        "total_hours": round(total_sec / 3600, 2),
        "productive_hours": round(prod_sec / 3600, 2),
        "unproductive_hours": round(unprod_sec / 3600, 2),
        "efficiency": round(total_eff, 1),
        "top_reasons": top_reasons,
        "sessions": session_details
    }