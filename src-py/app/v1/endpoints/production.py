from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, date, time, timedelta
from typing import Any, List, Optional
from pydantic import BaseModel

# Imports do Projeto
from app.db.session import get_db
from app import deps
from app.models.production_model import VehicleDailyMetric, EmployeeDailyMetric, ProductionOrder, ProductionSession, ProductionLog, AndonAlert, ProductionTimeSlice
from app.models.user_model import User
from app.services.production_service import ProductionService
from app.services.sap_sync import SAPIntegrationService
from app.schemas import production_schema, vehicle_schema, user_schema
from app.schemas.production_schema import SessionStart, SessionResponse, EmployeeStatsRead, ProductionAppointmentCreate, ProductionOrderRead, MachineDailyStats# Import do Modelo Vehicle (com fallback de nome)
try:
    from app.models.vehicle_model import Vehicle, VehicleStatus
except ImportError:
    from app.models.vehicle import Vehicle, VehicleStatus

router = APIRouter()

# --- MODEL LOCAL ---
class MachineStatusUpdate(BaseModel):
    machine_id: int
    status: str

class MachineDailyStats(BaseModel):
    date: str
    total_running_operator_seconds: float
    total_running_autonomous_seconds: float
    total_paused_operator_seconds: float
    total_maintenance_seconds: float
    total_idle_seconds: float
    
    # Campos novos para separar Setup de Pausa Comum
    total_setup_seconds: float     # <--- NOVO
    total_pause_seconds: float     # <--- NOVO
    
    formatted_running_operator: str
    formatted_running_autonomous: str
    formatted_paused_operator: str # Esse continua sendo a soma (Total)
    formatted_maintenance: str
    
    # Formatações novas
    formatted_setup: str           # <--- NOVO
    formatted_pause: str           # <--- NOVO


# ============================================================================
# 0. ESTATÍSTICAS DE FUNCIONÁRIOS (MOVIDO PARA CIMA PARA EVITAR ERRO 422)


@router.post("/closing/force")
async def force_daily_closing(
    target_date: date = None, 
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Força o cálculo e persistência das métricas para uma data específica.
    """
    if not target_date: target_date = date.today()
    
    # Roda ambos os processos
    users_count = await ProductionService.consolidate_daily_metrics(db, target_date)
    machines_count = await ProductionService.consolidate_machine_metrics(db, target_date)
    
    return {
        "message": "Fechamento Completo executado", 
        "date": target_date, 
        "processed": {"users": users_count, "machines": machines_count}
    }
@router.get("/reports/daily-closing", response_model=List[Any]) # Usando List[Any] para flexibilidade ou crie um Schema
async def get_daily_closing_report(
    target_date: date,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Busca o relatório consolidado (Snapshot) de um dia específico.
    É super rápido pois não calcula nada, apenas lê da tabela de métricas.
    """
    org_id = current_user.organization_id if current_user else 1
    
    # Busca na tabela de snapshot (EmployeeDailyMetric)
    query = select(EmployeeDailyMetric).where(
        EmployeeDailyMetric.date == target_date,
        EmployeeDailyMetric.organization_id == org_id
    ).order_by(desc(EmployeeDailyMetric.total_hours))
    
    # Precisamos fazer um join ou carregar o nome do usuário, 
    # pois a tabela de métricas só tem o user_id
    # Vamos fazer Eager Loading do User
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
            "top_reasons": row.top_reasons_snapshot, # Já é JSON
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
    
    # 1. Busca Operadores da Organização
    org_id = current_user.organization_id if current_user else 1
    query_users = select(User).where(User.organization_id == org_id)
    users = (await db.execute(query_users)).scalars().all()
    
    stats_list = []

    for user in users:
        # 2. Busca TODOS os logs onde este usuário foi o responsável
        # Ordenamos por máquina e tempo para reconstruir a linha do tempo
        q_logs = select(ProductionLog).where(
            ProductionLog.operator_id == user.id,
            ProductionLog.timestamp >= dt_start,
            ProductionLog.timestamp <= dt_end
        ).order_by(ProductionLog.vehicle_id, ProductionLog.timestamp)
        
        user_logs = (await db.execute(q_logs)).scalars().all()
        
        # Se não tem logs, pula
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

        # 3. Reconstrói a história
        # Para cada log do usuário, calculamos quanto tempo durou aquele status
        # até que QUALQUER OUTRO evento (dele, de outro ou do sistema) acontecesse na mesma máquina.
        
        for log in user_logs:
            # Busca o PRÓXIMO log desta mesma máquina (para saber quando o estado mudou)
            q_next = select(ProductionLog).where(
                ProductionLog.vehicle_id == log.vehicle_id,
                ProductionLog.timestamp > log.timestamp
            ).order_by(ProductionLog.timestamp.asc()).limit(1)
            
            next_log = (await db.execute(q_next)).scalars().first()
            
            # Se tem próximo log, calcula duração. Se não (é o atual), calcula até AGORA.
            end_time = next_log.timestamp if next_log else datetime.now()
            
            # Trava de segurança: Se a diferença for > 12h, provavelmente mudou turno/dia, ignoramos.
            duration = (end_time - log.timestamp).total_seconds()
            if duration > 43200: duration = 0 
            if duration < 0: duration = 0

            # --- CLASSIFICAÇÃO ---
            st = (log.new_status or "").upper()
            reason = (log.reason or "").upper()
            
            # Produtivo: OPERAÇÃO ou SETUP
            is_running = st in ["RUNNING", "EM OPERAÇÃO", "EM USO", "PRODUCING", "IN_USE"]
            is_setup = "SETUP" in st or "SETUP" in reason or "PREPARAÇÃO" in reason
            
            if is_running or is_setup:
                prod_sec += duration
            else:
                # Improdutivo: PARADA, MANUTENÇÃO, ETC.
                unprod_sec += duration
                
                # Conta motivo apenas se durou mais de 1 minuto (filtra ruído)
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
# 1. ESTATÍSTICAS DA MÁQUINA (CORRIGIDO ASYNC)
# ============================================================================
@router.get("/stats/{machine_id}", response_model=MachineDailyStats)
async def get_machine_stats(
    machine_id: int,
    target_date: date = None,
    db: AsyncSession = Depends(get_db)
):
    if not target_date:
        target_date = date.today()

    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)
    
    if target_date == date.today():
        end_of_day = datetime.now()

    # 1. Buscar último log ANTES do dia começar
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
    current_reason = last_log_before.reason if last_log_before else ""

    stats = {
        "running_op": 0.0,
        "running_auto": 0.0,
        "paused_productive": 0.0,
        "paused_unproductive": 0.0,
        "maintenance": 0.0,
        "idle": 0.0
    }

    timeline = []
    
    timeline.append({
        "time": start_of_day, 
        "status": current_status, 
        "has_op": is_operator_present,
        "reason": current_reason
    })

    for log in todays_logs:
        if log.event_type == 'LOGIN':
            is_operator_present = True
        elif log.event_type == 'LOGOUT':
            is_operator_present = False
        
        if log.new_status:
            current_status = log.new_status
        
        if log.reason:
            current_reason = log.reason

        timeline.append({
            "time": log.timestamp,
            "status": current_status,
            "has_op": is_operator_present,
            "reason": log.reason or ""
        })

    timeline.append({"time": end_of_day, "status": "IGNORE", "has_op": False, "reason": ""})

    for i in range(len(timeline) - 1):
        segment_start = timeline[i]
        segment_end = timeline[i+1]
        
        duration = (segment_end["time"] - segment_start["time"]).total_seconds()
        
        st = str(segment_start["status"]).upper()
        reason = str(segment_start.get("reason", "")).upper()
        op = segment_start["has_op"]

        # 1. MANUTENÇÃO
        if "MAINTENANCE" in st or "MANUTENÇÃO" in st or "MANUTENCAO" in st:
            stats["maintenance"] += duration
        
        # 2. RODANDO (PRODUÇÃO)
        elif "RUNNING" in st or "EM OPERAÇÃO" in st or "EM USO" in st or "IN_USE" in st:
            if op:
                stats["running_op"] += duration
            else:
                stats["running_auto"] += duration
        
        # 3. PAUSAS E SETUP (AQUI ESTAVA O PROBLEMA)
        # Adicionei "SETUP" e "EM PREPARAÇÃO" na verificação principal
        elif ("PAUSED" in st or "PARADA" in st or "STOPPED" in st or "AVAILABLE" in st or "DISPONÍVEL" in st or "SETUP" in st or "PREPARAÇÃO" in st):
            if op:
                # Classificação: O que é Produtivo vs Improdutivo
                # Se o status ou motivo for explicitamente SETUP, vai para paused_productive (Card Roxo)
                if "SETUP" in st or "SETUP" in reason or "PREPARAÇÃO" in reason or "MEDIÇÃO" in reason or "LIMPEZA" in reason:
                    stats["paused_productive"] += duration
                else:
                    # Pausa comum (Banheiro, etc) -> Card Laranja
                    stats["paused_unproductive"] += duration
            else:
                stats["idle"] += duration 
        
        else:
            stats["idle"] += duration

    total_paused = stats["paused_productive"] + stats["paused_unproductive"]

    def fmt(seconds):
        return str(timedelta(seconds=int(seconds)))

    return MachineDailyStats(
        date=str(target_date),
        total_running_operator_seconds=stats["running_op"],
        total_running_autonomous_seconds=stats["running_auto"],
        total_paused_operator_seconds=total_paused,
        total_maintenance_seconds=stats["maintenance"],
        total_idle_seconds=stats["idle"],
        
        # NOVOS CAMPOS
        total_setup_seconds=stats["paused_productive"],
        total_pause_seconds=stats["paused_unproductive"],

        formatted_running_operator=fmt(stats["running_op"]),
        formatted_running_autonomous=fmt(stats["running_auto"]),
        formatted_paused_operator=fmt(total_paused),
        formatted_maintenance=fmt(stats["maintenance"]),
        
        # NOVAS FORMATAÇÕES
        formatted_setup=fmt(stats["paused_productive"]),
        formatted_pause=fmt(stats["paused_unproductive"])
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
    db: AsyncSession = Depends(get_db)
):
    """
    Força o status para português para compatibilidade com o Dashboard.
    """
    print(f"🔄 [BACKEND] Mudança de Status Solicitada: {data.status} para Máquina ID: {data.machine_id}")

    query = select(Vehicle).where(Vehicle.id == data.machine_id)
    result = await db.execute(query)
    vehicle = result.scalars().first()
    
    if not vehicle:
        print("❌ Máquina não encontrada no banco.")
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    
    status_upper = str(data.status).strip().upper()
    
    # --- MAPEAMENTO PARA PORTUGUÊS (Compatibilidade Dashboard) ---
    new_status_db = "Disponível" 
    category_mes = "IDLE"

    # 1. EM USO / RODANDO
    if status_upper in ["RUNNING", "IN_USE", "EM USO", "EM OPERAÇÃO", "OPERANDO", "WORKING"]:
        new_status_db = "Em uso"
        category_mes = "PRODUCING"

    # 2. MANUTENÇÃO
    elif status_upper in ["MAINTENANCE", "BROKEN", "SETUP", "MANUTENÇÃO", "QUEBRADA", "MANUTENCAO", "EM MANUTENÇÃO"]:
        # Se você não tiver o Enum VehicleStatus importado, use a string direta: "Em manutenção"
        try:
            new_status_db = VehicleStatus.MAINTENANCE.value
        except:
            new_status_db = "Em manutenção"
        category_mes = "PLANNED_STOP"

    # 3. PARADA / PAUSA (CORREÇÃO AQUI)
    elif status_upper in ["STOPPED", "PAUSED", "PARADA", "EM PAUSA", "PAUSA"]:
        # Tenta pegar do Enum ou usa a string direta
        try:
            new_status_db = VehicleStatus.STOPPED.value
        except:
            new_status_db = "Parada"
        category_mes = "UNPLANNED_STOP"
            
    # 4. DISPONÍVEL (Padrão para AVAILABLE, IDLE, etc)
    else:
        # Tenta pegar do Enum ou usa a string direta
        try:
            new_status_db = VehicleStatus.AVAILABLE.value
        except:
            new_status_db = "Disponível"
        category_mes = "IDLE"

    print(f"✅ [BACKEND] Gravando no Banco: '{new_status_db}'")

    # Atualiza Veículo
    vehicle.status = new_status_db
    db.add(vehicle)
    
    # Atualiza Fatias de Tempo (MES)
    try:
        await ProductionService.close_current_slice(db, vehicle.id)
        await ProductionService.open_new_slice(db, vehicle.id, category=category_mes, reason=f"Status: {new_status_db}")
    except Exception as e:
        print(f"⚠️ [BACKEND] Erro ao atualizar fatia MES (não crítico): {e}")
    
    await db.commit()
    await db.refresh(vehicle)
    
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
# 6. REGISTRO DE EVENTOS (MES CORE) - COM DEBUGGER DETALHADO
# ============================================================================
@router.post("/event")
async def register_production_event(
    event: production_schema.ProductionEventCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    print(f"\n🔍 [PASSO 1] Recebido do Front: Tipo={event.event_type} | Badge='{event.operator_badge}'")

    try:
        # 1. Executa o serviço padrão
        result = await ProductionService.handle_event(db, event)
        print(f"🔍 [PASSO 2] Resultado do Service: {type(result)}")
        # print(f"   Dados: {result}") # Descomente se quiser ver o objeto inteiro

        # 2. Descobre o ID do Log e do Operador de forma segura
        log_id = None
        current_op_id = None

        if isinstance(result, dict):
            log_id = result.get('id')
            current_op_id = result.get('operator_id')
            print(f"   -> É um Dicionário. Log ID: {log_id} | Op ID: {current_op_id}")
        else:
            # Tenta pegar como atributo de objeto ou Pydantic model
            log_id = getattr(result, 'id', None)
            current_op_id = getattr(result, 'operator_id', None)
            print(f"   -> É um Objeto. Log ID: {log_id} | Op ID: {current_op_id}")

        # 3. Verifica se precisa corrigir
        raw_badge = str(event.operator_badge).strip() if event.operator_badge else ""
        
        if not current_op_id and raw_badge:
            print(f"⚠️ [FIX] Detectado Log sem Operador (System). Iniciando busca manual por: '{raw_badge}'")
            
            # Busca Usuário
            query_user = select(User).where(or_(
                User.employee_id == raw_badge,
                func.lower(User.email) == raw_badge.lower()
            ))
            res_user = await db.execute(query_user)
            user = res_user.scalars().first()
            
            if user:
                print(f"✅ [FIX] Usuário encontrado no DB: {user.full_name} (ID: {user.id})")
                
                if log_id:
                    # Busca o Log real no banco para editar
                    log_entry = await db.get(ProductionLog, log_id)
                    if log_entry:
                        log_entry.operator_id = user.id
                        db.add(log_entry)
                        await db.commit()
                        await db.refresh(log_entry)
                        print(f"🚀 [FIX] SUCESSO! Log {log_id} atualizado para User ID {user.id}")
                        
                        # Atualiza o resultado visual para retornar ao front correto
                        if isinstance(result, dict):
                            result['operator_id'] = user.id
                            result['operator_name'] = user.full_name
                        else:
                            # Se for objeto pydantic ou orm, tentamos atualizar
                            try:
                                result.operator_id = user.id
                                # Se tiver campo name no schema de resposta
                                if hasattr(result, 'operator_name'):
                                    result.operator_name = user.full_name
                            except:
                                pass
                    else:
                        print(f"❌ [FIX ERRO] Não consegui recarregar o Log ID {log_id} do banco.")
                else:
                    print("❌ [FIX ERRO] O serviço criou o log mas não retornou o ID dele.")
            else:
                print(f"❌ [FIX FALHA] Usuário NÃO encontrado no banco para o crachá '{raw_badge}'")
                
                # Debug Extra: Mostra quem está no banco pra conferir
                debug_q = select(User.employee_id, User.full_name).limit(5)
                d_res = await db.execute(debug_q)
                print(f"   (Amostra do banco: {d_res.all()})")
        
        elif current_op_id:
            print(f"✅ [OK] O log já foi criado com Operador ID: {current_op_id}. Nenhuma correção necessária.")
        else:
            print("ℹ️ [INFO] Sem crachá enviado ou log anônimo intencional.")

        return result

    except Exception as e:
        print(f"❌ [ERRO FATAL] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
        op_id = None # ID para o link
        if log.operator_id:
            op = await db.get(User, log.operator_id)
            if op: op_name = op.full_name or op.email
            op_id = op.id # Pega o ID real do usuário
            
        history.append({
            "id": log.id,
            "event_type": log.event_type,
            "timestamp": log.timestamp,
            "new_status": log.new_status,
            "reason": log.reason,
            "details": log.details,
            "operator_name": op_name,
            "operator_id": op_id # <--- CAMPO NOVO (Verifique seu Schema production_schema)
        })
        
    return history

# ============================================================================
# 8. SESSÕES (START/STOP) COM INTEGRAÇÃO MES
# ============================================================================
@router.post("/session/start", response_model=SessionResponse)
async def start_session(
    payload: SessionStart, 
    db: AsyncSession = Depends(deps.get_db)
):
    # --- ADICIONE ESTA LINHA AQUI ---
    op_code_str = str(payload.op_number)
    # --------------------------------
    
    print(f"🚀 [MES] Iniciando OP {op_code_str} - Etapa {payload.step_seq}")
    
    # 1. Busca a Máquina (Vehicle)
    machine = await db.get(Vehicle, payload.machine_id)
    if not machine: 
        raise HTTPException(status_code=404, detail="Máquina não encontrada")

    # 2. Busca o Operador
    user_q = await db.execute(select(User).where(or_(
        User.employee_id == payload.operator_badge,
        User.email == payload.operator_badge
    )))
    operator = user_q.scalars().first()
    if not operator: 
        raise HTTPException(status_code=404, detail="Operador não encontrado")

    # 3. Busca ou Cria a Ordem de Produção Local (Onde o op_code_str é usado)
    order_q = await db.execute(select(ProductionOrder).where(ProductionOrder.code == op_code_str))
    order = order_q.scalars().first()
    
    if not order:
        # Se não existe, busca no SAP para preencher o part_name (evitando o erro anterior)
        sap_service = SAPIntegrationService(db, organization_id=1)
        sap_op_data = await sap_service.get_production_order_by_code(op_code_str)
        
        part_name = "Item SAP"
        if sap_op_data:
            # Tenta pegar de objeto ou dicionário
            part_name = getattr(sap_op_data, 'part_name', sap_op_data.get('part_name', 'Item SAP'))

        order = ProductionOrder(
            code=op_code_str, 
            part_name=part_name, 
            status="SETUP",
            produced_quantity=0,
            scrap_quantity=0
        )
        db.add(order)
        await db.flush()
    # 4. Encerra qualquer sessão anterior pendente
    active_session_q = await db.execute(select(ProductionSession).where(
        ProductionSession.vehicle_id == machine.id,
        ProductionSession.end_time == None
    ))
    old_session = active_session_q.scalars().first()
    if old_session:
        old_session.end_time = datetime.now()
        db.add(old_session)

    # 5. Cria a Nova Sessão de Trabalho
    new_session = ProductionSession(
        vehicle_id=machine.id,
        user_id=operator.id,
        production_order_id=order.id,
        start_time=datetime.now()
    )
    db.add(new_session)
    await db.flush() 
    
    # 6. MES: Abre fatia de tempo
    await ProductionService.open_new_slice(
        db, 
        vehicle_id=machine.id, 
        category="PLANNED_STOP", 
        reason=f"Setup: {payload.step_seq}", 
        session_id=new_session.id,
        order_id=order.id
    )
    
    # 7. Atualiza Status
    machine.status = "Em manutenção" 
    order.status = "SETUP"
    
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Sessão iniciada: {payload.step_seq}",
        "session_id": str(new_session.id)
    }


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

@router.get("/reports/daily-closing/employees", response_model=List[Any])
async def get_daily_employee_report(
    target_date: date,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Retorna o histórico consolidado de OPERADORES para a data.
    """
    org_id = current_user.organization_id if current_user else 1
    
    query = select(EmployeeDailyMetric).options(selectinload(EmployeeDailyMetric.user)).where(
        EmployeeDailyMetric.date == target_date,
        EmployeeDailyMetric.organization_id == org_id
    ).order_by(desc(EmployeeDailyMetric.total_hours))
    
    results = (await db.execute(query)).scalars().all()
    
    report_data = []
    for row in results:
        # Garante que user não seja None para evitar erro
        user_name = "Desconhecido"
        if row.user:
            user_name = row.user.full_name or row.user.email
        
        report_data.append({
            "id": row.id,
            "user_id": row.user_id,
            "employee_name": user_name,
            "total_hours": row.total_hours,
            "productive_hours": row.productive_hours,
            "unproductive_hours": row.unproductive_hours,
            "efficiency": row.efficiency,
            "top_reasons": row.top_reasons_snapshot,
            "closed_at": row.closed_at
        })
        
    return report_data

@router.get("/reports/daily-closing/vehicles", response_model=List[Any])
async def get_daily_vehicle_report(
    target_date: date,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    org_id = current_user.organization_id if current_user else 1
    query = select(VehicleDailyMetric).options(selectinload(VehicleDailyMetric.vehicle)).where(
        VehicleDailyMetric.date == target_date,
        VehicleDailyMetric.organization_id == org_id
    ).order_by(desc(VehicleDailyMetric.running_hours))
    
    results = (await db.execute(query)).scalars().all()
    
    report = []
    for row in results:
        report.append({
            "id": row.id,
            "vehicle_name": f"{row.vehicle.brand} {row.vehicle.model}" if row.vehicle else f"ID {row.vehicle_id}",
            "running_hours": row.running_hours,
            "maintenance_hours": row.maintenance_hours,
            "idle_hours": row.idle_hours,
            "availability": row.availability,
            "utilization": row.utilization,
            "top_reasons": row.top_reasons_snapshot
        })
    return report