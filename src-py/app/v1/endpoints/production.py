from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_, and_, update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError  # <--- IMPORTANTE: Adicionado para tratar o erro
from datetime import datetime, date, time, timedelta
from typing import Any, List, Optional
from pydantic import BaseModel
from app.tasks.production_tasks import process_sap_appointment, task_fetch_open_orders, task_fetch_order_details


# Imports do Projeto
from app.db.session import get_db, async_session
from app import deps
from app.models.production_model import ProductionAppointment, MachineDailyMetric, EmployeeDailyMetric, ProductionOrder, ProductionSession, ProductionLog, ProductionTimeSlice
from app.models.user_model import User, UserRole
from app.services.fcm_service import enviar_push_lista
from app.services.production_service import ProductionService
from app.services.sap_sync import SAPIntegrationService
from app.schemas import production_schema, machine_schema, user_schema
from app.schemas.production_schema import SessionStart, SessionResponse, AppointmentCreate, EmployeeStatsRead, ProductionAppointmentCreate, ProductionOrderRead, MachineDailyStats
from app.models.andon_model import AndonCall
# Import do Modelo machine (com fallback de nome)

try:
    from app.models.machine_model import Machine, MachineStatus
except ImportError:
    from app.models.machine import Machine, MachineStatus

router = APIRouter()

# --- MODEL LOCAL ---
class MachineStatusUpdate(BaseModel):
    machine_id: int
    status: str
    reason: Optional[str] = None
    operator_badge: Optional[str] = None

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
    formatted_idle: str

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
    
    # Trava para o relógio não calcular horas no futuro (além do momento atual)
    now = datetime.now()
    if dt_end > now: dt_end = now
    
    org_id = current_user.organization_id if current_user else 1
    query_users = select(User).where(User.organization_id == org_id)
    users = (await db.execute(query_users)).scalars().all()
    
    stats_list = []
    
    # ✅ Filtro IDÊNTICO ao do gráfico Pareto da máquina
    IGNORED_LABELS = [
        "PARADA", "PAUSED", "STOPPED", "AVAILABLE", "DISPONÍVEL", "IDLE", 
        "OUTROS", "UNDEFINED", "SEM MOTIVO", "AGUARDANDO INÍCIO", "PENDING",
        "LOGOFF", "TROCA DE TURNO", "LOGOFF / TROCA DE TURNO", "MANUTENÇÃO GERAL",
        "OCIOSO", "OCIOSIDADE", "SETUP", "PREPARAÇÃO", "SAÍDA", "SAIDA",
        "STATUS:", "EM OPERAÇÃO", "RUNNING", "OPERAÇÃO", "SISTEMA", "111", "21",
        "ETAPA FINALIZADA", "FIM DE ETAPA", "PRODUÇÃO", "FIM DE MANUTENÇÃO"
    ]

    for user in users:
        # ✅ CORREÇÃO 1: Ordena a linha do tempo pelo crachá do operador de forma global
        q_logs = select(ProductionLog).where(
            ProductionLog.operator_id == user.id,
            ProductionLog.timestamp >= dt_start,
            ProductionLog.timestamp <= dt_end
        ).order_by(ProductionLog.timestamp.asc())
        
        user_logs = list((await db.execute(q_logs)).scalars().all())

        # --- 🚀 A MÁGICA DO EVENTO FANTASMA AQUI ---
        # Busca o último evento do operador ANTES da meia-noite de hoje
        q_last_before = select(ProductionLog).where(
            ProductionLog.operator_id == user.id,
            ProductionLog.timestamp < dt_start
        ).order_by(ProductionLog.timestamp.desc()).limit(1)
        
        last_before = (await db.execute(q_last_before)).scalars().first()
        
        # Se ele terminou o dia anterior trabalhando (não deu logout), insere o evento fantasma à 00:00
        if last_before:
            ev_type = str(last_before.event_type or "").upper()
            rsn = str(last_before.reason or "").upper()
            
            if ev_type not in ['LOGOUT', 'SESSION_END', 'LOGOFF'] and "SAÍDA" not in rsn:
                phantom = ProductionLog(
                    machine_id=last_before.machine_id,
                    operator_id=last_before.operator_id,
                    operator_badge=last_before.operator_badge,
                    operator_name=last_before.operator_name,
                    event_type=last_before.event_type,
                    new_status=last_before.new_status,
                    reason=last_before.reason,
                    details="[FANTASMA 00:00]",
                    timestamp=dt_start
                )
                user_logs.insert(0, phantom) # 👈 Adiciona na posição inicial (00:00)
        # -------------------------------------------
        
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

        # ✅ CORREÇÃO 2: Avança log por log do operador para achar o tempo real
        for i in range(len(user_logs)):
            log = user_logs[i]
            next_log = user_logs[i+1] if i + 1 < len(user_logs) else None
            
            # Se for o último log do dia, o tempo final é o momento atual
            next_time = next_log.timestamp if next_log else dt_end
            
            duration = (next_time - log.timestamp).total_seconds()
            if duration < 0: duration = 0
            
            # Se o intervalo for > 12h (Ex: Operador foi para casa e voltou no dia seguinte), ignoramos o buraco
            if duration > 43200: duration = 0 

            st = str(log.new_status or "").upper()
            reason = str(log.reason or "").strip()
            reason_upper = reason.upper()
            event_type = str(log.event_type or "").upper()
            
            # ----------------------------------------------------
            # A. TEMPO DESLOGADO (PERAMBULANDO / SEM MÁQUINA)
            # ----------------------------------------------------
            if event_type in ['LOGOUT', 'SESSION_END', 'LOGOFF'] or "SAÍDA" in reason_upper:
                # Tolerância de 10 minutos (600 segundos)
                if duration <= 600:
                    # Totalmente dentro da tolerância: joga para horas produtivas (transição)
                    prod_sec += duration
                else:
                    # Passou do limite: perdoa os primeiros 10 min e penaliza o excedente
                    prod_sec += 600
                    unprod_sec += (duration - 600)
                    
                continue

            # ----------------------------------------------------
            # B. TEMPO PRODUTIVO (OPERAÇÃO E SETUP)
            # ----------------------------------------------------
            is_running = any(x in st for x in ["RUNNING", "OPERAÇÃO", "USO", "PRODUCING"])
            is_setup = "SETUP" in st or "SETUP" in reason_upper or "PREPARAÇÃO" in reason_upper
            
            if is_running or is_setup:
                prod_sec += duration
            else:
            # ----------------------------------------------------
            # C. TEMPO PARADO (OFENSORES REAIS)
            # ----------------------------------------------------
                unprod_sec += duration
                
                # Baixámos de 60 para 5 segundos para que testes manuais entrem no ranking!
                if duration > 5: 
                    lbl = reason if reason else st
                    if lbl:
                        lbl_clean = lbl.replace("Parada: ", "").replace("Status: ", "").strip()
                        lbl_upper_clean = lbl_clean.upper()
                        
                        # Aplica a lista negra do Pareto
                        if not any(ignored in lbl_upper_clean for ignored in IGNORED_LABELS) and not "SETUP" in lbl_upper_clean:
                            # Conta +1 vez que ele usou este motivo
                            reasons_map[lbl_clean] = reasons_map.get(lbl_clean, 0) + 1

        total_sec = prod_sec + unprod_sec
        efficiency = (prod_sec / total_sec * 100) if total_sec > 0 else 0.0
        
        # Gera o ranking dos 3 motivos mais selecionados
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
    
    # Ordena a lista de operadores por quem trabalhou mais horas
    stats_list.sort(key=lambda x: x['total_hours'], reverse=True)
    return stats_list

# ============================================================================
# 1. ESTATÍSTICAS DA MÁQUINA (CORRIGIDO PARA NOVA ARQUITETURA)
# ============================================================================
@router.get("/stats/{machine_id}/history")
async def get_machine_history_metrics(machine_id: int, days: int = 30, db: AsyncSession = Depends(deps.get_db)):
    """
    Devolve o histórico de performance (OEE, Produtividade) 
    dos últimos X dias para os gráficos da página de Detalhes.
    """
    start_date = date.today() - timedelta(days=days)
    
    query = select(MachineDailyMetric).where(
        MachineDailyMetric.machine_id == machine_id,
        MachineDailyMetric.date >= start_date
    ).order_by(MachineDailyMetric.date.asc())
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return metrics
@router.get("/stats/{machine_id}", response_model=MachineStatsRealTime)
async def get_machine_stats(machine_id: int, target_date: date = None, db: AsyncSession = Depends(get_db)):
    if not target_date: target_date = date.today()
    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)
    if target_date == date.today(): end_of_day = datetime.now()

    # 1. VERIFICA SESSÃO ATIVA
    q_session = select(ProductionSession).where(
        ProductionSession.machine_id == machine_id,
        ProductionSession.start_time < start_of_day,
        or_(ProductionSession.end_time == None, ProductionSession.end_time >= start_of_day)
    )
    active_session_start = (await db.execute(q_session)).scalars().first()
    is_operator_present = active_session_start is not None

    # 2. STATUS INICIAL
    stmt_last_st = select(ProductionLog).filter(
        ProductionLog.machine_id == machine_id,
        ProductionLog.timestamp < start_of_day,
        ProductionLog.new_status.isnot(None)
    ).order_by(ProductionLog.timestamp.desc()).limit(1)
    
    last_st = (await db.execute(stmt_last_st)).scalars().first()
    current_status = last_st.new_status if last_st else "IDLE"
    current_reason = last_st.reason if last_st else ""

    # 3. LOGS DO DIA
    stmt_logs = select(ProductionLog).filter(
        ProductionLog.machine_id == machine_id,
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
        elif st in ["SETUP", "PREPARAÇÃO", "PLANNED_STOP"]:
            stats["setup"] += duration

        # 3. PRODUÇÃO (Verde ou Azul)
        elif st in ["RUNNING", "EM OPERAÇÃO", "EM USO", "PRODUCING", "1", "IN_USE", "PRODUÇÃO AUTÔNOMA", "IN_USE_AUTONOMOUS"]:
            if "AUTÔNOMA" in st or "AUTONOMOUS" in st or not op:
                stats["running_auto"] += duration
            else: 
                stats["running_op"] += duration 
        
        # 4. OCIOSIDADE (Card Cinza) - Prioridade Máxima
        # Se o status gritar Ocioso OU o motivo contiver a palavra mágica
        elif st in ["OCIOSO", "OCIOSIDADE", "AVAILABLE", "DISPONÍVEL", "IDLE"] or "DISPONÍVEL" in reason or "LIBERADA" in reason:
            stats["idle"] += duration
            
        # 5. PARADAS (Card Laranja e Preto)
        elif st in ["PAUSED", "PARADA", "STOPPED", "PAUSADA", "0", "UNPLANNED_STOP", "MICRO_STOP"]:
            if st == "MICRO_STOP" or duration < 300:
                stats["micro_stop"] += duration
            else:
                stats["pause"] += duration
        
        # Fallback de segurança: Qualquer coisa não mapeada vira ocioso
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
        formatted_micro_stop=fmt(stats["micro_stop"]),
        formatted_idle=fmt(stats["idle"]) 
    )

@router.get("/history/{machine_id}")
async def get_machine_history(machine_id: int, skip: int = 0, limit: int = 100, event_type: Optional[str] = None, db: AsyncSession = Depends(deps.get_db)):
    # 👇 Voltou a consultar a tabela de LOGS
    query = select(ProductionLog).where(ProductionLog.machine_id == machine_id)
    if event_type: query = query.where(ProductionLog.event_type == event_type)
    query = query.order_by(desc(ProductionLog.timestamp)).offset(skip).limit(limit)

    logs = (await db.execute(query)).scalars().all()
    history = []
    for log in logs:
        history.append({
            "id": log.id,
            "event_type": log.event_type,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "new_status": log.new_status,
            "reason": log.reason,
            "details": log.details,
            "operator_name": log.operator_name or "Sistema",
            "operator_id": log.operator_id,
            "operator_badge": log.operator_badge
        })
    return history

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
        "LOGOFF", "TROCA DE TURNO", "LOGOFF / TROCA DE TURNO", "MANUTENÇÃO GERAL", "Manutenção Geral",
        "OCIOSO", "OCIOSIDADE", "SETUP", "PREPARAÇÃO", "SAÍDA", "SAIDA",
        "ETAPA FINALIZADA", "FIM DE ETAPA", "PRODUÇÃO", "EM USO", "RUNNING", "OPERAÇÃO"
    ]

    # ---------------------------------------------------------
    # NOVA LÓGICA: APENAS DADOS CONSOLIDADOS PELO CELERY
    # (Removido o cálculo em tempo real de "Hoje")
    # ---------------------------------------------------------
    query_history = select(MachineDailyMetric).where(
        MachineDailyMetric.machine_id == machine_id,
        MachineDailyMetric.date >= start_date,
        MachineDailyMetric.date <= today # Permite incluir hoje, caso tenha rolado um fechamento forçado
    )
    metrics_history = (await db.execute(query_history)).scalars().all()
    
    total_running = sum(m.running_hours for m in metrics_history)
    total_setup = sum(m.planned_stop_hours for m in metrics_history)
    total_pause = sum(m.idle_hours for m in metrics_history)
    total_maintenance = sum(m.maintenance_hours for m in metrics_history)
    total_micro_stops = sum(m.micro_stop_hours for m in metrics_history)
    total_idle = sum(m.idle_hours for m in metrics_history)  
    total_pause = sum(m.pause_hours for m in metrics_history) 
    reasons_hours_map = {}
    for m in metrics_history:
        for entry in (m.top_reasons_snapshot or []):
            lbl = entry.get('label', '').strip()
            hours = float(entry.get('hours', 0))
            
            if not lbl: continue
            
            lbl_upper = lbl.upper()
            
            # 🚀 CORREÇÃO AQUI: Em vez de procurar o texto exato, 
            # ele agora vasculha se a frase CONTÉM alguma das palavras proibidas!
            if any(ignored in lbl_upper for ignored in IGNORED_LABELS): 
                continue
                
            reasons_hours_map[lbl] = reasons_hours_map.get(lbl, 0) + hours

    sum_avail_history = sum(m.availability for m in metrics_history)
    count_history = len(metrics_history)
    
    # Média real baseada apenas nos dias já processados
    final_avg_availability = (sum_avail_history / count_history) if count_history > 0 else 0.0

    sorted_stops = sorted([{"name": k, "value": round(v, 2)} for k, v in reasons_hours_map.items() if v > 0.01], key=lambda x: x['value'], reverse=True)
    avg_mtbf = round(sum(m.mtbf for m in metrics_history) / count_history, 1) if count_history > 0 else 0
    avg_mttr = round(sum(m.mttr for m in metrics_history) / count_history, 1) if count_history > 0 else 0

    return {
        "total_running": round(total_running, 2), # 👈 Agora 1 min será 0.02h
        "total_setup": round(total_setup, 2),
        "total_pause": round(total_pause, 2),         # Card Laranja
        "total_idle": round(total_idle, 2),           # Card Cinza
        "total_maintenance": round(total_maintenance, 2),
        "total_micro_stops": round(total_micro_stops, 2), 
        "avg_availability": round(final_avg_availability, 1),
        "stop_reasons": sorted_stops[:10],
        "mtbf": avg_mtbf,
        "mttr": avg_mttr
    }
@router.post("/consolidate/{machine_id}")
async def force_machine_consolidation(machine_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # 1. Busca a máquina e a Sessão Ativa
        machine = await db.get(Machine, machine_id)
        if not machine: raise HTTPException(404, "Máquina não encontrada")
        
        active_session_q = await db.execute(select(ProductionSession).where(
            ProductionSession.machine_id == machine_id, 
            ProductionSession.end_time == None
        ))
        active_sess = active_session_q.scalars().first()
        sess_id = active_sess.id if active_sess else None
        ord_id = active_sess.production_order_id if active_sess else None

        # 🚀 O SEGREDO DO "TRANSBORDO": Pega a fatia que ESTÁ ABERTA agora, ANTES de fechar ela.
        active_slice = await ProductionService.get_active_slice(db, machine_id)
        
        category_mes = active_slice.category if active_slice else "IDLE"
        reason_mes = active_slice.reason if active_slice else f"Status: {machine.status}"

        # 2. FECHA a fatia de tempo atual exatamente AGORA
        now = datetime.now()
        await ProductionService.close_current_slice(db, machine_id, now)
        
        # 3. ABRE a nova fatia como um "clone" da anterior, continuando o trabalho perfeitamente
        await ProductionService.open_new_slice(
            db, 
            machine_id, 
            category=category_mes, 
            reason=reason_mes,
            session_id=sess_id, 
            order_id=ord_id
        )
        
        # 4. AGORA SIM CONSOLIDA! (A fatia anterior foi fechada, logo o tempo Produtivo entra no cálculo)
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
    from app.core.websocket_manager import manager 
    from app.schemas.production_schema import ProductionEventCreate
    
    print(f"🔄 [BACKEND] Mudança Manual: {data.status} | Motivo: {data.reason} -> Máquina {data.machine_id}")

    machine = await db.get(Machine, data.machine_id)
    if not machine: raise HTTPException(404, "Máquina não encontrada")
    
    status_upper = str(data.status).strip().upper()
    
    # 🚀 O NOVO "TRADUTOR" DE MOTIVOS VISUAIS
    final_reason = data.reason
    if not final_reason:
        if status_upper in ["STOPPED", "PAUSED", "PARADA", "0"]:
            final_reason = "SEM MOTIVO"
        elif status_upper in ["MAINTENANCE", "EM MANUTENÇÃO", "QUEBRADA"]:
            final_reason = "Máquina em manutenção"
        elif status_upper in ["AVAILABLE", "IDLE", "DISPONÍVEL", "DISPONIVEL"]:
            final_reason = "Máquina disponível"
        elif status_upper in ["SETUP", "PREPARAÇÃO", "PLANNED_STOP"]:
            final_reason = "Preparação / Setup"
        elif status_upper in ["1", "RUNNING", "EM OPERAÇÃO", "EM USO", "PRODUCING", "IN_USE"]:
            final_reason = "Em uso"
        elif status_upper in ["IN_USE_AUTONOMOUS", "PRODUÇÃO AUTÔNOMA", "AUTÔNOMO"]:
            final_reason = "Produção Autônoma"
        else:
            final_reason = "Alteração de Status"

    # 🚀 A CORREÇÃO ESTÁ AQUI:
    # Se o frontend não mandar um crachá, assumimos que foi o "SISTEMA" (Admin no tablet)
    # Assim a Trava do Arduino não bloqueia a liberação da máquina!
    badge_to_use = data.operator_badge if data.operator_badge else "SISTEMA"

    event_payload = ProductionEventCreate(
        machine_id=machine.id,
        operator_badge=badge_to_use, # 👈 MUDOU AQUI!
        event_type="STATUS_CHANGE",
        new_status=status_upper,
        timestamp=datetime.now(),
        reason=final_reason 
    )

    try:
        result = await ProductionService.handle_event(db, event_payload)
        await db.refresh(machine)
        cat_mes = result.get("category", "IDLE")
        
        await manager.broadcast({
            "type": "MACHINE_STATE_CHANGED",
            "machine_id": machine.id,
            "new_status": cat_mes,
            "machine_status_db": machine.status
        }, org_id=machine.organization_id)
        
        return {"message": "Status atualizado", "new_status": machine.status}
        
    except Exception as e:
        print(f"❌ Erro ao aplicar status manual: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class MachineLayoutUpdate(BaseModel):
    machine_id: int
    layout_x: float
    layout_y: float

@router.post("/machine/layout")
async def update_machine_layout(data: MachineLayoutUpdate, db: AsyncSession = Depends(get_db)):
    """Atualiza a posição X e Y da máquina na tela de Supervisório."""
    machine = await db.get(Machine, data.machine_id)
    if not machine: 
        raise HTTPException(404, "Máquina não encontrada")
    
    machine.layout_x = data.layout_x
    machine.layout_y = data.layout_y
    
    db.add(machine)
    await db.commit()
    return {"status": "success", "message": "Layout salvo com sucesso."}

# ============================================================================
# 4. LISTAR MÁQUINAS
# ============================================================================
# ✅ CORREÇÃO AQUI: Mudado de machine_schema.machine para machine_schema.MachinePublic
@router.get("/machines", response_model=List[machine_schema.MachinePublic])
async def read_machines(db: AsyncSession = Depends(deps.get_db), skip: int = 0, limit: int = 100):
    query = select(Machine).offset(skip).limit(limit)
    machines = (await db.execute(query)).scalars().all()
    return machines

# ============================================================================
# 5. ANDON (ALERTAS)
# ============================================================================
@router.post("/andon")
async def open_andon_alert(alert: production_schema.AndonCreate, db: AsyncSession = Depends(deps.get_db)):
    machine = await db.get(Machine, alert.machine_id)
    if not machine: raise HTTPException(404, "Machine not found")

    query_op = select(User).where(or_(User.employee_id == alert.operator_badge, User.email == alert.operator_badge))
    operator = (await db.execute(query_op)).scalars().first()
    if not operator: raise HTTPException(404, "Operator not found")

    # 🚀 CORREÇÃO AQUI: Mudado para AndonCall, apontando pra organização 1 e com os enums certos!
    new_alert = AndonCall(
        organization_id=1, # Adicionado suporte a organização
        machine_id=machine.id, 
        operator_id=operator.id, 
        sector=alert.sector, # O SQLAlchemy converte string pra SAEnum automaticamente se o nome bater
        description=alert.notes, # Mudou de 'notes' para 'description'
        status="OPEN"
    )
    db.add(new_alert)
    
    db.add(ProductionLog(
        machine_id=machine.id, 
        operator_id=operator.id,        
        operator_badge=operator.employee_id, 
        operator_name=operator.full_name,    
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
        
        result = await ProductionService.handle_event(db, event)
        
        # 🚀 1. BUSCA A ORGANIZAÇÃO DA MÁQUINA NO BANCO
        query = await db.execute(select(Machine.organization_id).where(Machine.id == int(event.machine_id)))
        org_id = query.scalars().first() or 1  # Usa 1 como fallback de segurança
        
        # 🚀 2. ADICIONA O org_id NO BROADCAST
        await manager.broadcast({
            "type": "MACHINE_STATE_CHANGED",
            "machine_id": int(event.machine_id),
            "new_status": event.new_status,
            "category": result.get("category"),
            "machine_status_db": result.get("new_machine_status")
        }, org_id=org_id) # <-- CORREÇÃO AQUI
        
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
        )
        .where(
            ProductionAppointment.machine_id == machine_id,
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
    query = select(ProductionLog).where(ProductionLog.machine_id == machine_id)
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
    op_code_str = str(payload.op_number).strip()
    print(f"🚀 [MES] Recebendo pedido de OP {op_code_str} - Etapa {payload.step_seq}")
    
    # 🔒 1. TRAVA DE CONCORRÊNCIA (PESSIMISTIC LOCK)
    # with_for_update() obriga requisições simultâneas a formarem uma fila.
    # A Requisição 2 vai pausar nesta linha até a Requisição 1 dar o commit final.
    q_machine = select(Machine).where(Machine.id == payload.machine_id).with_for_update()
    machine = (await db.execute(q_machine)).scalars().first()
    
    if not machine: raise HTTPException(404, "Máquina não encontrada")

    user_q = await db.execute(select(User).where(or_(User.employee_id == payload.operator_badge, User.email == payload.operator_badge)))
    operator = user_q.scalars().first()
    if not operator: raise HTTPException(404, "Operador não encontrado")

    machine_id_safe = machine.id
    operator_id_safe = operator.id
    operator_name_safe = operator.full_name

    # 2. Busca ou Cria a Ordem
    order_q = await db.execute(select(ProductionOrder).where(ProductionOrder.code == op_code_str))
    order = order_q.scalars().first()
    
    if not order:
        try:
            sap_service = SAPIntegrationService(db, organization_id=1)
            sap_op_data = await sap_service.get_production_order_by_code(op_code_str)
            part_name = getattr(sap_op_data, 'part_name', 'Item SAP') if sap_op_data else "Item SAP"

            new_order = ProductionOrder(code=op_code_str, part_name=part_name)
            db.add(new_order)
            await db.flush() 
            order = new_order
        except IntegrityError:
            await db.rollback()
            order_retry = await db.execute(select(ProductionOrder).where(ProductionOrder.code == op_code_str))
            order = order_retry.scalars().first()
            if not order: raise HTTPException(500, "Erro crítico de concorrência: Ordem não encontrada.")

    # 3. Verifica Sessão Anterior (AGORA A TRAVA FUNCIONA)
    # Como a Requisição 2 esperou a 1 terminar, ela VAI achar a sessão aqui e ser bloqueada!
    active_session_q = await db.execute(select(ProductionSession).where(
        ProductionSession.machine_id == machine_id_safe, 
        ProductionSession.end_time == None
    ))
    old_session = active_session_q.scalars().first()

    # --- PROTEÇÃO CONTRA DUPLO CLIQUE REAL ---
    if old_session and old_session.production_order_id == order.id and old_session.user_id == operator_id_safe:
        print(f"ℹ️ [MES] Bloqueado. Sessão já ativa (Duplo clique evitado).")
        # Liberamos o cadeado do banco sem fazer nada
        await db.commit() 
        return {"status": "success", "message": f"Sessão já iniciada", "session_id": str(old_session.id)}

    if old_session:
        old_session.end_time = datetime.now()
        db.add(old_session)

    # 4. Cria Nova Sessão
    new_session = ProductionSession(
        machine_id=machine_id_safe, 
        user_id=operator_id_safe, 
        production_order_id=order.id, 
        start_time=datetime.now()
    )
    db.add(new_session)
    await db.flush() 
    
    # 5. Fecha a fatia anterior (Provavelmente o IDLE gerado no login)
    await ProductionService.close_current_slice(db, machine_id_safe)

    # 6. Registra Fatia de Tempo e Log
    await ProductionService.open_new_slice(
        db, 
        machine_id=machine_id_safe, 
        category="PLANNED_STOP", 
        reason=f"Setup: {payload.step_seq}", 
        session_id=new_session.id, 
        order_id=order.id
    )
    
    await db.execute(update(Machine).where(Machine.id == machine_id_safe).values(status="Setup"))
    
    log = ProductionLog(
        machine_id=machine_id_safe, 
        operator_id=operator_id_safe, 
        operator_badge=str(payload.operator_badge),
        operator_name=operator_name_safe,
        event_type="STATUS_CHANGE", 
        new_status="Setup",
        reason="Setup Inicial",
        details=f"{order.code} - Posição: {payload.step_seq}", 
        timestamp=datetime.now()
    )
    db.add(log)

    # 7. COMMIT FINAL: Salva tudo e SOLTA O CADEADO para a próxima requisição!
    await db.commit()
    
    # 8. Avisa o Frontend via WebSocket
    from app.core.websocket_manager import manager
    await manager.broadcast({
        "type": "MACHINE_STATE_CHANGED",
        "machine_id": machine_id_safe,
        "new_status": "PLANNED_STOP",
        "machine_status_db": "Setup"
    }, org_id=1)

    return {"status": "success", "message": f"Sessão iniciada", "session_id": str(new_session.id)}
@router.post("/session/stop")
async def stop_session(data: production_schema.SessionStopSchema, db: AsyncSession = Depends(deps.get_db)):
    # 1. Busca a sessão ativa
    q = select(ProductionSession).where(
        ProductionSession.machine_id == data.machine_id, 
        ProductionSession.end_time == None
    )
    session = (await db.execute(q)).scalars().first()
    
    if not session: 
        return {"status": "error", "message": "No active session"}

    end_time = datetime.now()
    machine = await db.get(Machine, session.machine_id)
    
    # ---------------------------------------------------------------------
    # 🚀 CORREÇÃO DA HISTÓRIA AUTOMÁTICA ("O TRUQUE DO FINALIZAR")
    # ---------------------------------------------------------------------
    # Se a máquina foi pausada (Sem Motivo) e logo em seguida a sessão foi encerrada,
    # assumimos que o operador pausou apenas para apertar "Finalizar Etapa / Deslogar".
    active_slice = await ProductionService.get_active_slice(db, machine.id)
    is_finishing_from_pause = False

    if machine.status == MachineStatus.STOPPED.value and active_slice and active_slice.category == "UNPLANNED_STOP":
        reason_upper = str(active_slice.reason or "").upper()
        
        if reason_upper in ["SEM MOTIVO", "PARADA", "STATUS: PARADA", ""]:
            is_finishing_from_pause = True
            
            # 1. Transforma o tempo da pausa genérica em tempo produtivo de finalização
            active_slice.category = "PRODUCING"
            active_slice.reason = "Operador finalizou a etapa"
            db.add(active_slice)
            
            # 2. Corrige a tabela de Logs (Front) para sumir a "PAUSADA - SEM MOTIVO" e virar DISPONÍVEL
            stmt_last_log = select(ProductionLog).where(
                ProductionLog.machine_id == machine.id
            ).order_by(desc(ProductionLog.timestamp)).limit(1)
            
            last_log = (await db.execute(stmt_last_log)).scalars().first()
            
            if last_log and last_log.new_status == MachineStatus.STOPPED.value:
                last_log.new_status = MachineStatus.AVAILABLE.value
                last_log.reason = "Etapa finalizada pelo operador"
                db.add(last_log)
                
            # Atualiza a máquina antecipadamente para o Motor de Estados ignorar conflitos a seguir
            machine.status = MachineStatus.AVAILABLE.value

    # 2. Fecha a fatia de tempo atual no MES (Aquela atrelada ao operador)
    await ProductionService.close_current_slice(db, data.machine_id, end_time)

    # 3. Busca todas as fatias de tempo geradas ao longo desta sessão
    slices_q = select(ProductionTimeSlice).where(ProductionTimeSlice.session_id == session.id)
    slices = (await db.execute(slices_q)).scalars().all()
    
    productive_sec = 0
    unproductive_sec = 0

    # 4. Varre fatia por fatia classificando os tempos
    for s in slices:
        cat = s.category
        reason = str(s.reason or "").upper()
        
        if cat == 'PRODUCING' or "SETUP" in reason or "PREPARAÇÃO" in reason:
            productive_sec += s.duration_seconds
        elif cat in ['UNPLANNED_STOP', 'MAINTENANCE'] or "PARADA" in reason:
            unproductive_sec += s.duration_seconds

    # 5. Salva os cálculos na sessão
    total_duration = int((end_time - session.start_time).total_seconds())
    session.end_time = end_time
    session.duration_seconds = total_duration
    session.productive_seconds = int(productive_sec)
    session.unproductive_seconds = int(unproductive_sec)
    
    # ---------------------------------------------------------------------
    # 🚀 6. O FIM DO BURACO NEGRO (Garante a continuidade da linha do tempo)
    # ---------------------------------------------------------------------
    if machine:
        if machine.status == MachineStatus.MAINTENANCE.value or machine.status == "Em manutenção":
            await ProductionService.open_new_slice(
                db, 
                machine_id=machine.id, 
                category="MAINTENANCE", 
                reason="Máquina em manutenção",
                session_id=None, 
                order_id=None
            )
        else:
            # Encerramento normal, máquina fica Disponível.
            machine.status = MachineStatus.AVAILABLE.value
            
            # Texto inteligente baseado no que aconteceu
            idle_reason = "Etapa finalizada pelo operador" if is_finishing_from_pause else "Máquina Disponível (Fim de Sessão)"
            
            await ProductionService.open_new_slice(
                db, 
                machine_id=machine.id, 
                category="IDLE", 
                reason=idle_reason, 
                session_id=None, 
                order_id=None
            )
            
            # Avisa o painel (Gantt) que a máquina liberou e ficou cinza
            from app.core.websocket_manager import manager
            await manager.broadcast({
                "type": "MACHINE_STATE_CHANGED",
                "machine_id": machine.id,
                "new_status": "IDLE",
                "machine_status_db": machine.status
            }, org_id=getattr(machine, 'organization_id', 1))

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
@router.get("/session/active/{machine_id}")
async def get_active_session(machine_id: int, db: AsyncSession = Depends(deps.get_db)):
    """Busca a O.P. e o Operador que estão rodando na máquina neste exato momento."""
    
    # 1. Busca a sessão ativa (Apenas com o user, sem o production_order no selectinload)
    query = select(ProductionSession).options(
        selectinload(ProductionSession.user)
    ).where(
        ProductionSession.machine_id == machine_id,
        ProductionSession.end_time.is_(None)
    )
    
    session = (await db.execute(query)).scalars().first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Nenhuma sessão ativa encontrada")
        
    # 2. Busca a O.P. manualmente pelo ID (Estratégia segura)
    order_data = None
    if session.production_order_id:
        order = await db.get(ProductionOrder, session.production_order_id)
        if order:
            order_data = {
                "id": order.id,
                "code": order.code,
                "part_name": getattr(order, 'part_name', 'N/A'),
                "status": getattr(order, 'status', 'N/A'),
                # A MÁGICA ESTÁ AQUI: Envia o custom_ref para o front!
                "custom_ref": getattr(order, 'custom_ref', None) 
            }
            
    return {
        "session_id": session.id,
        "start_time": session.start_time,
        "operator": {
            "id": session.user.id if session.user else None,
            "full_name": session.user.full_name if session.user else None,
            "employee_id": session.user.employee_id if session.user else None
        } if session.user else None,
        "order": order_data
    }
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
        machine = await db.get(Machine, sess.machine_id)
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
            machine = await db.get(Machine, machine_id)
            machine_name = f"{machine.brand} {machine.model}" if machine else f"Máquina {machine_id}"
            roles_alvo = [UserRole.MAINTENANCE, UserRole.PCP, UserRole.MANAGER, UserRole.ADMIN]
            query = select(User.device_token).where(User.organization_id == org_id, User.role.in_(roles_alvo), User.device_token.isnot(None))
            tokens = (await db.execute(query)).scalars().all()
            if tokens:
                linha_ordem = f"\nO.S.: {op_number}" if str(op_number).upper().startswith("OS-") else f"\nO.P.: {op_number}"
                if not op_number: linha_ordem = ""
                enviar_push_lista(tokens=list(tokens), title="🛑 MÁQUINA PARADA", body=f"{machine_name} parou.\nMotivo: {motivo}{linha_ordem}", data={"tipo": "manutencao", "machineId": str(machine_id)})
        except Exception as e: print(f"❌ Erro ao notificar quebra: {e}")

from app.tasks.production_tasks import process_sap_appointment, task_fetch_open_orders, task_fetch_order_details

# ============================================================================
# 10. INTEGRAÇÃO SAP (ASYNC CELERY)
# ============================================================================

@router.post("/appoint", status_code=status.HTTP_202_ACCEPTED)
async def create_appointment(
    data: ProductionAppointmentCreate, 
    db: AsyncSession = Depends(deps.get_db), 
    current_user: Optional[User] = Depends(deps.get_current_active_user)
):
    org_id = current_user.organization_id if current_user else 1
    appointment_dict = data.model_dump() if hasattr(data, 'model_dump') else data.dict()
    
    # 🚀 Joga para o Celery fazer o trabalho pesado de rede com o SAP!
    process_sap_appointment.delay(appointment_data=appointment_dict, organization_id=org_id)
    
    # Responde imediatamente pro Tablet
    return {"message": "Apontamento na fila de processamento do SAP", "status": "processing"}


@router.get("/orders/open", status_code=status.HTTP_202_ACCEPTED)
async def get_open_orders(machine_id: int = 0):
    # 🚀 O FastAPI não vai mais esperar o SAP buscar todas as OPs. 
    if machine_id > 0:
        task_fetch_open_orders.delay(machine_id=machine_id)
        
    return {"message": "Buscando no SAP. Aguarde retorno via WebSocket.", "status": "processing"}


@router.get("/orders/{code}", status_code=status.HTTP_202_ACCEPTED)
async def get_production_order(code: str, machine_id: int = 0):
    # 🚀 Dispara a busca e avisa para aguardar
    if machine_id > 0:
        task_fetch_order_details.delay(code=code, machine_id=machine_id)
        
    return {"message": "Buscando detalhes no SAP.", "status": "processing"}

@router.get("/history/user/{user_id}")
async def get_user_production_history(user_id: int, db: AsyncSession = Depends(deps.get_db), current_user: User = Depends(deps.get_current_active_user)):
    user = await db.get(User, user_id)
    if not user or not user.employee_id: return []
    
    badge = str(user.employee_id)
    
    # Query usando o novo campo operator_badge e appointment_type
    stmt = select(ProductionAppointment, Machine).outerjoin(
        Machine, ProductionAppointment.machine_id == Machine.id
    ).where(
        and_(
            ProductionAppointment.operator_badge == badge, 
            ProductionAppointment.appointment_type == "PRODUCTION"
        )
    ).order_by(desc(ProductionAppointment.start_time)).limit(2000)
    
    result = await db.execute(stmt)
    history = []
    
    for appointment, machine in result.all():
        duration_min = int((appointment.end_time - appointment.start_time).total_seconds() / 60) if appointment.start_time and appointment.end_time else 0
        
        
        history.append({
            "id": appointment.id, 
            "machine_name": f"{machine.brand} {machine.model}" if machine else f"Máquina #{appointment.machine_id}",
            "op_number": appointment.sap_doc_num or "N/A",  # Novo campo
            "step": appointment.sap_position or "",         # Novo campo
            "start_time": appointment.start_time.isoformat() if appointment.start_time else None,
            "end_time": appointment.end_time.isoformat() if appointment.end_time else None,
            "duration_minutes": duration_min, 
        })
        
    return history

@router.post("/internal/broadcast")
async def internal_broadcast(payload: dict):
    """
    Rota interna usada pelo Celery para avisar o FastAPI
    para disparar mensagens no WebSocket.
    """
    from app.core.websocket_manager import manager
    
    # 🚀 1. EXTRAI A ORGANIZAÇÃO DO PACOTE (Se não vier, usa 1 por segurança para não quebrar)
    org_id = payload.get("org_id") or payload.get("organization_id") or 1
    
    print(f"📣 [PONTE] Repassando evento do Celery para WebSockets (Org {org_id}): {payload.get('type')}")
    
    # 🚀 2. PASSA O org_id AQUI!
    await manager.broadcast(payload, org_id=org_id)
    
    return {"status": "broadcasted"}

@router.get("/search")
async def global_search(q: str, db: AsyncSession = Depends(deps.get_db)):
    """
    Busca global: Vasculha Ordens de Produção, Máquinas e Operadores.
    """
    if len(q) < 2:
        return []

    results = []
    search_term = f"%{q}%"

    # 1. Buscar Ordens de Produção (O.S. / O.P.)
    query_orders = select(ProductionOrder).where(
        or_(
            ProductionOrder.code.ilike(search_term),
            ProductionOrder.part_name.ilike(search_term)
        )
    ).limit(5)
    orders = (await db.execute(query_orders)).scalars().all()
    
    for order in orders:
        # Verifica se essa O.P. está rodando em alguma máquina agora
        active_session_query = select(ProductionSession).options(selectinload(ProductionSession.machine)).where(
            ProductionSession.production_order_id == order.id,
            ProductionSession.end_time.is_(None)
        )
        active_session = (await db.execute(active_session_query)).scalars().first()
        
        # Textos e Rotas padrão (Caso a O.S. já tenha encerrado ou não tenha começado)
        sublabel = f"Peça: {getattr(order, 'part_name', 'N/A')} | Status: {getattr(order, 'status', 'N/A')}"
        route_url = f"/production/orders/{order.id}" # Rota fallback (se for clicar numa O.S antiga)

        # Se a O.S estiver ativa em alguma máquina, a mágica acontece aqui:
        if active_session and active_session.machine:
            sublabel = f"🔴 RODANDO AGORA na {active_session.machine.brand} {active_session.machine.model}"
            # MUDA A ROTA PARA A TELA DE EMPLOYEES DA MÁQUINA ATUAL!
            route_url = f"/employees?machine={active_session.machine.id}"

        results.append({
            "id": order.id,
            "type": "order",
            "label": f"O.S: {order.code}",
            "sublabel": sublabel,
            "icon": "assignment",
            "color": "teal-9" if not active_session else "red-10",
            "route": route_url
        })

    # 2. Buscar Máquinas (machines)
    query_machines = select(Machine).where(
        or_(
            Machine.brand.ilike(search_term),
            Machine.model.ilike(search_term)
            # Retiramos a busca por "plate" aqui!
        )
    ).limit(5)
    machines = (await db.execute(query_machines)).scalars().all()
    
    for mac in machines:
        results.append({
            "id": mac.id,
            "type": "machine",
            "label": f"Máquina: {mac.brand} {mac.model}",
            "sublabel": f"Status atual: {mac.status}",
            "icon": "precision_manufacturing",
            "color": "blue-9",
            "route": f"/employees?machine={mac.id}" 
        })

    # 3. Buscar Operadores (Users)
    query_users = select(User).where(
        or_(
            User.full_name.ilike(search_term),
            User.employee_id.ilike(search_term)
        )
    ).limit(5)
    users = (await db.execute(query_users)).scalars().all()
    
    for user in users:
        results.append({
            "id": user.id,
            "type": "user",
            "label": f"Operador: {user.full_name}",
            "sublabel": f"Matrícula: {user.employee_id or 'N/A'}",
            "icon": "badge",
            "color": "orange-9",
            "route": f"/users/{user.id}/stats"
        })

    return results


@router.get("/tracker/{op_code}")
async def get_digital_traveler(op_code: str, db: AsyncSession = Depends(deps.get_db)):
    """
    RG DIGITAL DA PEÇA (Digital Traveler)
    Busca tudo sobre a OP/OS no SAP e cruza com o histórico local do MES.
    """
    # 1. BUSCA O "RG" NO SAP (Material, Quantidade, Desenho e Roteiro)
    sap_service = SAPIntegrationService(db, organization_id=1)
    sap_data = await sap_service.get_production_order_by_code(op_code)

    if not sap_data:
        raise HTTPException(status_code=404, detail="Ordem não encontrada no SAP.")

    # 2. BUSCA O "HISTÓRICO CRIMINAL" NO MES (Onde ela já passou)
    # Trata o código para achar tanto OS (OS-4595-1) quanto OP (4595)
    doc_num_search = op_code.split('-')[1] if str(op_code).startswith("OS-") else op_code

    stmt_apts = select(ProductionAppointment, Machine).outerjoin(
        Machine, ProductionAppointment.machine_id == Machine.id
    ).where(
        or_(
            ProductionAppointment.sap_doc_num == op_code,
            ProductionAppointment.sap_doc_num == doc_num_search
        )
    ).order_by(ProductionAppointment.start_time.asc())

    result_apts = await db.execute(stmt_apts)
    appointments = result_apts.all()

    # 3. MONTA A LINHA DO TEMPO BRUTA
    timeline = []
    for apt, machine in appointments:
        dur_sec = (apt.end_time - apt.start_time).total_seconds() if apt.start_time and apt.end_time else 0
        timeline.append({
            "id": apt.id,
            "step_seq": apt.sap_position,
            "operator": apt.sap_operator_name or apt.operator_badge,
            "machine": f"{machine.brand} {machine.model}" if machine else "Bancada/Manual",
            "start_time": apt.start_time,
            "end_time": apt.end_time,
            "duration_minutes": round(max(0, dur_sec) / 60, 1),
            "type": apt.appointment_type,  # PRODUCTION, SETUP, STOP
            "produced_qty": getattr(apt, 'target_qty', 0)
        })

    # 4. CRUZA O HISTÓRICO COM O ROTEIRO (Para saber o progresso da peça)
    steps = sap_data.get("steps", [])
    total_time_op = 0.0

    for step in steps:
        # Pega só o que aconteceu nesta etapa específica
        step_apts = [t for t in timeline if str(t["step_seq"]) == str(step["seq"])]
        
        step_time = sum(t["duration_minutes"] for t in step_apts if t["type"] == "PRODUCTION")
        total_time_op += step_time

        if step_apts:
            step["status"] = "IN_PROGRESS"
            step["history"] = step_apts
            step["time_spent"] = step_time
        else:
            step["status"] = "PENDING"
            step["history"] = []
            step["time_spent"] = 0.0

    # 5. DESCOBRE ONDE A PEÇA ESTÁ AGORA
    current_step = None
    # Vai de trás pra frente ou pega a última etapa que teve ação
    for step in reversed(steps):
        if step["status"] == "IN_PROGRESS":
            current_step = step["seq"]
            break
    
    # Se não achou nada em progresso, marca a primeira como atual
    if current_step is None and steps:
        current_step = steps[0]["seq"]

    # 6. ENTREGA O PACOTE COMPLETO PARA O VUE.JS
    return {
        "header": {
            "op_number": sap_data["op_number"],
            "item_code": sap_data["item_code"],
            "part_name": sap_data["part_name"],
            "planned_qty": sap_data["planned_qty"],
            "uom": sap_data["uom"],
            "custom_ref": sap_data["custom_ref"],
            "drawing_code": sap_data["drawing"], # Esse é o código que o Celery vai usar pra buscar o PDF!
            "is_service": sap_data.get("is_service", False),
            "total_time_spent_min": round(total_time_op, 1)
        },
        "current_step_seq": current_step,
        "routing": steps
    }