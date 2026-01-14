from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, case
from datetime import date, datetime, time
from typing import List, Optional

from app import crud, models
from app import deps

# Import Schemas
from app.schemas import production_schema, vehicle_schema

# Import Models
from app.models.production_model import ProductionLog, ProductionOrder, AndonAlert, ProductionSession
from app.models.vehicle_model import Vehicle, VehicleStatus
from app.models.user_model import User

router = APIRouter()

# --- NEW ENDPOINT: List Machines (ASYNC) ---
@router.get("/machines", response_model=List[vehicle_schema.VehiclePublic])
async def read_machines(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Lists all machines (vehicles) asynchronously.
    """
    query = select(Vehicle).offset(skip).limit(limit)
    result = await db.execute(query)
    machines = result.scalars().all()
    return machines

@router.post("/andon")
async def open_andon_alert(
    alert: production_schema.AndonCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    # Validate Machine
    machine = await db.get(Vehicle, alert.machine_id)
    if not machine: raise HTTPException(404, "Machine not found")

    # Validate Operator
    query_op = select(User).where(User.email == alert.operator_badge)
    result_op = await db.execute(query_op)
    operator = result_op.scalars().first()
    
    if not operator and alert.operator_badge == "BADGE-123":
        res = await db.execute(select(User).limit(1))
        operator = res.scalars().first()
    
    if not operator: raise HTTPException(404, "Operator not found")

    # Create Alert
    new_alert = AndonAlert(
        vehicle_id=machine.id,
        operator_id=operator.id,
        sector=alert.sector,
        notes=alert.notes,
        status="OPEN"
    )
    db.add(new_alert)
    
    # Register Log as well
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

# --- 1. RECEIVE KIOSK EVENTS (ASYNC) ---
# --- MAIN FIX: STATUS MAPPING ---
@router.post("/event")
async def register_production_event(
    event: production_schema.ProductionEventCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    # A. Validate Machine
    machine = await db.get(Vehicle, event.machine_id)
    if not machine: raise HTTPException(404, "Machine not found")

    # B. Validate Operator
    query_op = select(User).where(User.email == event.operator_badge)
    result_op = await db.execute(query_op)
    operator = result_op.scalars().first()
    
    if not operator and event.operator_badge == "BADGE-123":
        res = await db.execute(select(User).limit(1))
        operator = res.scalars().first()
    
    if not operator: raise HTTPException(404, "Operator not found")

    # C. Process P.O.
    order = None
    if event.order_code:
        res_order = await db.execute(select(ProductionOrder).where(ProductionOrder.code == event.order_code))
        order = res_order.scalars().first()
        if order:
            if event.event_type == 'COUNT':
                order.produced_quantity += (event.quantity_good or 0)
                order.scrap_quantity += (event.quantity_scrap or 0)
                db.add(order)
            if event.new_status == 'RUNNING': order.status = 'RUNNING'
            elif event.new_status == 'STOPPED': order.status = 'PAUSED'
            db.add(order)

    # D. Update Machine Status (Strict Mapping)
    if event.new_status:
        print(f"\n[DEBUG] --- Received Status Event ---")
        print(f"[DEBUG] Status from Cockpit: '{event.new_status}'")
        
        status_map = {
            # COCKPIT       ->  DATABASE (Legacy Fleet)
            "RUNNING":      "IN_USE",       # Running = In Use (Green)
            "SETUP":        "MAINTENANCE",  # Setup = Maintenance (Red)
            
            # FIX: "STOPPED" (Paused) now becomes "AVAILABLE" (Yellow/Waiting)
            # This solves your complaint that paused was turning into maintenance
            "STOPPED":      "AVAILABLE",    
            "IDLE":         "AVAILABLE",
            "AVAILABLE":    "AVAILABLE",
            "OFFLINE":      "AVAILABLE"
        }
        
        # Get mapped status
        db_status = status_map.get(event.new_status)
        print(f"[DEBUG] Mapped to Database: '{db_status}'")
        
        if db_status:
            # Check current status before changing
            print(f"[DEBUG] PREVIOUS Status in DB: '{machine.status}'")
            machine.status = db_status 
            db.add(machine)
            print(f"[DEBUG] NEW Status saved in object: '{machine.status}'")
        else:
            print(f"[DEBUG] ALERT: Status '{event.new_status}' not found in map! Nothing changed.")
            
        print(f"[DEBUG] ----------------------------------\n")

    # E. Log
    log_entry = ProductionLog(
        vehicle_id=machine.id,
        operator_id=operator.id,
        order_id=order.id if order else None,
        event_type=event.event_type,
        reason=event.reason,
        details=event.details,
        new_status=event.new_status, # Saves ORIGINAL status (e.g. SETUP) for history
        previous_status=machine.status,
        timestamp=datetime.now()
    )
    db.add(log_entry)
    
    await db.commit()
    return {"status": "success"}

@router.get("/history/{machine_id}", response_model=List[production_schema.ProductionLogRead])
async def get_machine_history(
    machine_id: int,
    skip: int = 0,
    limit: int = 20,
    event_type: Optional[str] = None, # Optional filter
    db: AsyncSession = Depends(deps.get_db)
):
    query = select(ProductionLog).where(ProductionLog.vehicle_id == machine_id)
    
    # Dynamic Filter
    if event_type:
        query = query.where(ProductionLog.event_type == event_type)
        
    # Sort and Pagination
    query = query.order_by(desc(ProductionLog.timestamp)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Response assembly (with operator name hack)
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

# --- 2. GET/CREATE P.O. (ASYNC) ---
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
            status="PENDING",
            part_image_url="https://images.unsplash.com/photo-1616422285623-13ff0162193c?auto=format&fit=crop&w=1000&q=80"
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
    return order

# --- 3. SESSION MANAGEMENT (START/STOP) ---

@router.post("/session/start")
async def start_session(
    data: production_schema.SessionStartSchema,
    db: AsyncSession = Depends(deps.get_db)
):
    # 1. Validate Machine
    machine = await db.get(Vehicle, data.machine_id)
    if not machine: raise HTTPException(404, "Invalid Machine")

    # 2. Validate Operator
    res = await db.execute(select(User).where(User.email == data.operator_badge))
    operator = res.scalars().first()
    if not operator: 
        # Fallback for demo
        if data.operator_badge == "BADGE-123":
            res = await db.execute(select(User).limit(1))
            operator = res.scalars().first()
        if not operator: raise HTTPException(404, "Invalid Badge")

    # 3. Validate P.O.
    res_ord = await db.execute(select(ProductionOrder).where(ProductionOrder.code == data.order_code))
    order = res_ord.scalars().first()
    if not order: raise HTTPException(404, "P.O. not found")

    # 4. Close previous session if exists (safety)
    active_session_q = await db.execute(select(ProductionSession).where(
        ProductionSession.vehicle_id == machine.id,
        ProductionSession.end_time == None
    ))
    old_session = active_session_q.scalars().first()
    if old_session:
        old_session.end_time = datetime.now()
        db.add(old_session)

    # 5. Create New Session
    new_session = ProductionSession(
        vehicle_id=machine.id,
        user_id=operator.id,
        production_order_id=order.id,
        start_time=datetime.now()
    )
    db.add(new_session)
    
    # Update machine status to SETUP (standard start)
    # Important: In the DB, Setup = MAINTENANCE (Red)
    machine.status = VehicleStatus.MAINTENANCE 
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
    # 1. Find active session
    q = select(ProductionSession).where(
        ProductionSession.vehicle_id == data.machine_id,
        ProductionSession.end_time == None
    )
    res = await db.execute(q)
    session = res.scalars().first()
    
    if not session:
        return {"status": "error", "message": "No active session"}

    # 2. Define end
    end_time = datetime.now()
    session.end_time = end_time

    # 3. CALCULATION ALGORITHM WITH TOLERANCE
    # Search logs for this session
    logs_q = select(ProductionLog).where(
        ProductionLog.vehicle_id == data.machine_id,
        ProductionLog.timestamp >= session.start_time
    ).order_by(ProductionLog.timestamp)
    
    logs_res = await db.execute(logs_q)
    logs = logs_res.scalars().all()

    total_prod = 0.0
    total_unprod = 0.0
    
    # Starting point
    cursor_time = session.start_time
    # Assume starts in SETUP (Unproductive but subject to analysis)
    # Rule: Only RUNNING generates direct productivity.
    current_status = "SETUP" 

    # Add a virtual "final" event to close the last interval
    virtual_logs = list(logs)
    virtual_logs.append(ProductionLog(timestamp=end_time, new_status="SESSION_END"))

    for log in virtual_logs:
        # Calculate duration of previous interval up to this event
        delta = (log.timestamp - cursor_time).total_seconds()
        
        if delta > 0:
            # Check if previous status was productive
            if current_status == "RUNNING" or current_status == "IN_USE":
                # If running, it's 100% productive
                total_prod += delta
            else:
                # If STOPPED (STOPPED, SETUP, MAINTENANCE, IDLE)
                # Check 5 minute tolerance (300 seconds)
                if delta <= 300:
                    # Tolerance: counts as productive (bathroom, quick adjustment)
                    total_prod += delta
                else:
                    # Exceeded tolerance: counts as unproductive
                    total_unprod += delta
        
        # Update cursor
        cursor_time = log.timestamp
        if log.new_status != "SESSION_END":
            # Update status for next iteration
            current_status = log.new_status or current_status

    session.duration_seconds = int((end_time - session.start_time).total_seconds())
    session.productive_seconds = int(total_prod)
    session.unproductive_seconds = int(total_unprod)

    # 4. Release machine
    machine = await db.get(Vehicle, session.vehicle_id)
    # Set to AVAILABLE (Yellow)
    machine.status = VehicleStatus.AVAILABLE
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

# --- 4. ENDPOINT FOR EMPLOYEE REPORT ---
@router.get("/stats/employees", response_model=List[production_schema.EmployeeStatsRead])
async def get_employee_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(deps.get_db)
):
    # 1. Definição do Range de Datas (Padrão: Mês Atual)
    if not start_date: start_date = date.today().replace(day=1)
    if not end_date: end_date = date.today()
    
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)

    users = (await db.execute(select(User))).scalars().all()
    stats_list = []

    for user in users:
        # Busca sessões que aconteceram neste período
        query = select(ProductionSession).where(
            ProductionSession.user_id == user.id,
            ProductionSession.start_time <= dt_end,
            (ProductionSession.end_time >= dt_start) | (ProductionSession.end_time == None)
        )
        sessions = (await db.execute(query)).scalars().all()

        if not sessions:
            # Retorna zerado se não trabalhou no período
            stats_list.append({
                "employee_name": user.full_name or user.email,
                "total_hours": 0, "productive_hours": 0, "unproductive_hours": 0,
                "efficiency": 0, "top_reasons": []
            })
            continue

        # Somatória Real
        total_sec = sum(s.duration_seconds for s in sessions)
        prod_sec = sum(s.productive_seconds for s in sessions)
        unprod_sec = sum(s.unproductive_seconds for s in sessions)
        
        # Para sessões abertas (em tempo real), calcula o parcial até AGORA
        now = datetime.now()
        for s in sessions:
            if s.end_time is None:
                current_duration = (now - s.start_time).total_seconds()
                total_sec += current_duration
                # Simplificação para lista geral: Assume eficiência atual proporcional ou projeta
                # Para ser 100% preciso, precisaria reprocessar logs, mas para lista geral isso pesa.
                # Vamos assumir que o tempo decorrido conta no total para mostrar atividade.

        efficiency = (prod_sec / total_sec * 100) if total_sec > 0 else 0

        # Query de Motivos (Apenas os Top 3 para a lista resumida)
        # Busca logs de paradas dentro das sessões do período
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

# --- 5. ENDPOINT: DETALHES COMPLETOS DO FUNCIONÁRIO (MICRO) ---
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

    # 1. Recuperar Sessões Detalhadas
    # Faz join com Vehicle e ProductionOrder para pegar nomes
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
        # Carrega relacionamentos (lazy load no async exige cuidado, idealmente usar options(joinedload))
        # Aqui faremos fetch simples para garantir
        machine = await db.get(Vehicle, s.vehicle_id)
        order = await db.get(ProductionOrder, s.production_order_id) if s.production_order_id else None
        
        # Recalcula tempo real se estiver aberta
        dur = s.duration_seconds
        prod = s.productive_seconds
        unprod = s.unproductive_seconds
        
        if s.end_time is None:
            dur = (datetime.now() - s.start_time).total_seconds()
            # Na aberta, não temos prod/unprod consolidado no DB ainda, usamos 0 ou estimativa
            # Para o relatório detalhado, mostramos status "Em Andamento"
        
        total_sec += dur
        prod_sec += prod
        unprod_sec += unprod
        
        eff = (prod / dur * 100) if dur > 0 else 0
        
        # Formata duração hh:mm:ss
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

    # 2. Pareto Real de Motivos (Agregado por Tempo e Quantidade)
    # Soma o tempo que ficou parado em cada motivo (Isso é BI de verdade)
    # Obs: Como não temos duração no Log, vamos contar ocorrências (mais seguro pra agora)
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
                "duration_minutes": 0 # Implementar futuramente diff de logs
            })

    # 3. Totais Gerais
    total_eff = (prod_sec / total_sec * 100) if total_sec > 0 else 0

    return {
        "total_hours": round(total_sec / 3600, 2),
        "productive_hours": round(prod_sec / 3600, 2),
        "unproductive_hours": round(unprod_sec / 3600, 2),
        "efficiency": round(total_eff, 1),
        "top_reasons": top_reasons,
        "sessions": session_details
    }