from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, date, time
from typing import List, Optional
from pydantic import BaseModel
from app.crud import crud_vehicle
from app.db.session import get_db
from app.services.sap_sync import SAPIntegrationService
from app.schemas.production_schema import ProductionAppointmentCreate, ProductionOrderRead
# Imports do Projeto
from app.models.production_model import ProductionOrder as ProductionOrderModel
from app import deps 
from app.schemas import production_schema, vehicle_schema
from app.models.production_model import ProductionLog, ProductionOrder, AndonAlert, ProductionSession, ProductionTimeSlice
from app.models.user_model import User
from app.services.production_service import ProductionService # <--- NOVO SERVIÇO

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
# 1. ROTA DE STATUS DA MÁQUINA (Manual Override)
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
    
    if not operator: raise HTTPException(404, "Operator not found")

    new_alert = AndonAlert(
        vehicle_id=machine.id,
        operator_id=operator.id,
        sector=alert.sector,
        notes=alert.notes,
        status="OPEN"
    )
    db.add(new_alert)
    
    # Log simples
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
# 4. REGISTRO DE EVENTOS (MES CORE)
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
    
    # Join manual para pegar nome do operador (pode ser otimizado com joinedload no futuro)
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
# 6. SESSÕES (START/STOP) COM INTEGRAÇÃO MES
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
    if not operator: raise HTTPException(404, "Invalid Badge")

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
        # Fecha fatia e sessão
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
    
    # 3. MES: Abre primeira fatia como SETUP/MANUTENÇÃO
    # Geralmente começa preparando a máquina
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
    
    # 2. MES: Fecha última fatia de tempo
    await ProductionService.close_current_slice(db, data.machine_id, end_time)

    # 3. CÁLCULO PRECISO BASEADO NAS FATIAS (TIME SLICES)
    # Em vez de iterar logs, somamos as durações das fatias desta sessão
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
    
    # 4. Libera Máquina
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
# 7. RELATÓRIOS & OEE (NOVO)
# ============================================================================

@router.get("/stats/machine/{machine_id}/oee")
async def get_machine_oee(
    machine_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Calcula o OEE baseado nas fatias de tempo geradas pelo MES.
    """
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
        # Busca Sessões do Usuário
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

        # Top motivos de parada (Baseado em Time Slices é mais preciso, mas usando logs por enquanto para compatibilidade)
        # Idealmente: Agrupar ProductionTimeSlice.reason where session_id in sessions...
        
        stats_list.append({
            "id": user.id, 
            "employee_name": user.full_name or user.email,
            "total_hours": round(total_sec / 3600, 2),
            "productive_hours": round(prod_sec / 3600, 2),
            "unproductive_hours": round(unprod_sec / 3600, 2),
            "efficiency": round(efficiency, 1),
            "top_reasons": [] # Implementar agregação se necessário
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
    """
    Retorna o histórico detalhado de sessões de um operador em um período.
    Usado para montar o 'Dossiê Mensal' e calcular eficiência por mês.
    """
    # Converter para datetime (Início do dia -> Fim do dia)
    dt_start = datetime.combine(start_date, time.min)
    dt_end = datetime.combine(end_date, time.max)

    # Busca sessões do usuário no range
    query = select(ProductionSession).where(
        ProductionSession.user_id == user_id,
        ProductionSession.start_time >= dt_start,
        ProductionSession.start_time <= dt_end
    ).order_by(desc(ProductionSession.start_time))

    result = await db.execute(query)
    sessions = result.scalars().all()
    
    session_details = []
    
    for sess in sessions:
        # Busca máquina para mostrar nome
        machine = await db.get(Vehicle, sess.vehicle_id)
        
        # Busca ordem para mostrar código
        order_code = "---"
        if sess.production_order_id:
            order = await db.get(ProductionOrder, sess.production_order_id)
            if order: order_code = order.code
            
        # Calcula Eficiência da Sessão
        total = sess.duration_seconds
        prod = sess.productive_seconds
        efficiency = (prod / total * 100) if total > 0 else 0
        
        # Formata Duração
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
            "time_slices": [] # Não precisamos carregar slices detalhados aqui para não pesar
        })
        
    return session_details

@router.post("/appoint")
async def create_appointment(
    data: ProductionAppointmentCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    # Não buscamos mais vehicle_id no banco. Usamos o resource_code direto.
    resource_code = data.resource_code
    
    # Garante que o operador seja limpo (remove email se vier por engano)
    # Se vier "vitor@vemag", tentamos limpar ou usamos o que vier se for numérico
    sap_employee_id = data.operator_id
    if "@" in sap_employee_id:
        # Se for email, isso é um erro de processo, mas tentamos evitar o crash
        # Ideal: O frontend deve mandar o crachá certo.
        print(f"⚠️ AVISO: Recebido email no operador ({sap_employee_id}).") 
        
    sap_service = SAPIntegrationService(db, organization_id=1)
    
    try:
        appointment_dict = data.model_dump()
    except AttributeError:
        appointment_dict = data.dict()
    
    # Passamos o resource_code direto
    success = await sap_service.create_production_appointment(
        appointment_dict, 
        sap_resource_code=resource_code
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao registrar no SAP")
    
    return {"message": "Apontamento realizado!"}

@router.get("/orders/open", response_model=List[ProductionOrderRead])
async def get_open_orders(
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Retorna a lista de OPs liberadas direto do SAP.
    """
    sap_service = SAPIntegrationService(db, organization_id=1)
    
    # Busca OPs liberadas no SAP
    orders = await sap_service.get_released_production_orders()
    
    return orders

# ============================================================================
# 2. ROTA DE OP ÚNICA (DINÂMICA)
# ============================================================================
@router.get("/orders/{code}", response_model=ProductionOrderRead)
async def get_production_order(
    code: str, 
    db: AsyncSession = Depends(deps.get_db)
):
    # 1. Busca Localmente (Cache) -> Usando o MODEL aqui
    query = select(ProductionOrderModel).where(ProductionOrderModel.code == code)
    result = await db.execute(query)
    order = result.scalars().first()
    
    # 2. Se não existir, busca no SAP
    if not order:
        print(f"🔎 Buscando OP {code} no SAP...")
        
        sap_service = SAPIntegrationService(db, organization_id=1)
        sap_data = await sap_service.get_production_order_by_code(code)
        
        if sap_data:
            print(f"💾 Sincronizando OP {code} para o banco local...")
            
            # 3. Cria o objeto Local -> Usando o MODEL aqui
            order = ProductionOrderModel(
                code=str(sap_data['op_number']),
                part_name=sap_data['part_name'],
                part_code=sap_data['item_code'],
                target_quantity=sap_data['quantity'],
                status="PENDING",
                produced_quantity=0,
                scrap_quantity=0,
                part_image_url="" 
            )
            
            db.add(order)
            await db.commit()
            await db.refresh(order)
        else:
            raise HTTPException(status_code=404, detail="OP não encontrada no SAP")
            
    return order