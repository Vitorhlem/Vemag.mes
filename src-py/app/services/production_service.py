from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any

# Models
from app.models.production_model import MachineDailyMetric, EmployeeDailyMetric, ProductionLog, ProductionOrder, ProductionSession, ProductionTimeSlice
from app.models.machine_model import Machine, MachineStatus
from app.models.user_model import User

# Schemas
from app.schemas.production_schema import ProductionEventCreate


class ProductionService:
    
    @staticmethod
    async def get_active_slice(db: AsyncSession, machine_id: int) -> Optional[ProductionTimeSlice]:
        """Busca a fatia de tempo que está aberta (sem end_time) para a máquina."""
        query = select(ProductionTimeSlice).where(
            ProductionTimeSlice.machine_id == machine_id,
            ProductionTimeSlice.end_time == None
        ).order_by(desc(ProductionTimeSlice.start_time))
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def close_current_slice(db: AsyncSession, machine_id: int, end_time: datetime = None):
        """Fecha a fatia atual aplicando a regra de micro-parada APENAS para pausas comuns."""
        if not end_time: end_time = datetime.now()
        current_slice = await ProductionService.get_active_slice(db, machine_id)
        
        if current_slice:
            current_slice.end_time = end_time
            delta = (end_time - current_slice.start_time).total_seconds()
            current_slice.duration_seconds = int(max(0, delta))
            
            # --- NOVA REGRA RESTRITA DA MICRO-PARADA ---
            # Só vira MICRO_STOP se a categoria original for UNPLANNED_STOP
            # Se for PRODUCING, MAINTENANCE, IDLE ou PLANNED_STOP (Setup), não mexe!
            if current_slice.category == "UNPLANNED_STOP" and 0 < delta < 300:
                reason_upper = (current_slice.reason or "").upper()
                # Não sobrescreve se o operador já justificou com algo importante
                if "SETUP" not in reason_upper and "MANUTENÇÃO" not in reason_upper:
                    current_slice.category = "MICRO_STOP"
                    current_slice.reason = f"Micro-parada: {current_slice.reason or 'Parada curta'}"
            
            db.add(current_slice)
            await db.commit()
            return current_slice
        return None

    @staticmethod
    async def open_new_slice(
        db: AsyncSession, 
        machine_id: int, 
        category: str, 
        reason: Optional[str] = None,
        session_id: Optional[int] = None,
        order_id: Optional[int] = None
    ) -> ProductionTimeSlice:
        """Abre uma nova fatia de tempo mantendo a transação atual com flush."""
        is_productive = category in ["PRODUCING", "PLANNED_STOP"]
        
        new_slice = ProductionTimeSlice(
            machine_id=machine_id,
            start_time=datetime.now(),
            category=category,
            reason=reason,
            is_productive=is_productive,
            session_id=session_id,
            order_id=order_id
        )
        db.add(new_slice)
        await db.flush() 
        return new_slice

    @staticmethod
    async def handle_event(db: AsyncSession, event: ProductionEventCreate) -> Dict[str, Any]:
        """
        MOTOR DE ESTADOS ESTRITO: 
        Gerencia o ciclo de vida da máquina garantindo 0 lixo no banco.
        """
        timestamp = datetime.now()
        machine = await db.get(Machine, event.machine_id)
        if not machine: raise ValueError("Machine not found")

        sinal_recebido = str(event.new_status).upper() if event.new_status else ""
        
        # --- 1. IDENTIFICAÇÃO DO OPERADOR & REGRA DO DESPERTAR ---
        badge = str(event.operator_badge or "").strip()
        user_id = None
        user_name = "Sistema"

        # Busca sessão ativa
        stmt_session = select(ProductionSession).where(
            ProductionSession.machine_id == machine.id,
            ProductionSession.end_time == None
        ).order_by(desc(ProductionSession.start_time)).limit(1)
        active_session = (await db.execute(stmt_session)).scalars().first()

        if badge == "ESP32_HARDWARE" or not badge:
            if active_session:
                user_q = await db.execute(select(User).where(User.id == active_session.user_id))
                user = user_q.scalars().first()
                if user:
                    user_id = user.id
                    user_name = user.full_name
                    badge = user.employee_id 
            else:
                # Se o sinal veio do Hardware e NINGUÉM logou, a máquina é um fantasma e o sinal é ignorado.
                print(f"🛑 [MOTOR] Sinal '{sinal_recebido}' descartado. Nenhuma OP ativa na Máquina {machine.id}.")
                return {"status": "ignored", "reason": "Sinal de hardware descartado pois não há Sessão ativa."}
        else:
            # Evento vindo do Tablet com crachá
            user_q = await db.execute(select(User).where(or_(User.employee_id == badge, User.email == badge)))
            user = user_q.scalars().first()
            if user:
                user_id = user.id
                user_name = user.full_name

        last_log_status = machine.status

        # --- 2. TRADUTOR DE SINAL PARA ESTADO & CATEGORIA (STRICT MODE) ---
        new_status_enum = MachineStatus.STOPPED 
        category = "UNPLANNED_STOP" 

        # A: Disponível (Fim de O.P, Login Inicial, Pós-Manutenção)
        if sinal_recebido in ["AVAILABLE", "DISPONÍVEL", "DISPONIVEL", "IDLE", "OCIOSO"]:
            new_status_enum = MachineStatus.AVAILABLE 
            category = "IDLE"
            if not event.reason or event.reason == "null":
                event.reason = "Máquina Disponível"

        # B: Setup
        elif sinal_recebido in ["SETUP", "PREPARAÇÃO", "PLANNED_STOP"]:
            new_status_enum = MachineStatus.SETUP
            category = "PLANNED_STOP"

        # C: Produção
        elif sinal_recebido in ["1", "RUNNING", "EM OPERAÇÃO", "PRODUCING", "EM USO", "IN_USE"]:
            if last_log_status == MachineStatus.IN_USE_AUTONOMOUS.value:
                new_status_enum = MachineStatus.IN_USE_AUTONOMOUS
            else:
                new_status_enum = MachineStatus.IN_USE
            category = "PRODUCING"

        # D: Parada Não Planejada
        elif sinal_recebido in ["0", "STOPPED", "PAUSADA", "PARADA"]:
            new_status_enum = MachineStatus.STOPPED
            category = "UNPLANNED_STOP"
            if not event.reason or event.reason == "null":
                event.reason = "SEM MOTIVO"

        # E: Manutenção
        elif sinal_recebido in ["MAINTENANCE", "EM MANUTENÇÃO", "QUEBRADA"]:
            new_status_enum = MachineStatus.MAINTENANCE
            category = "MAINTENANCE"
            
        # F: Autônomo
        elif sinal_recebido in ["IN_USE_AUTONOMOUS", "PRODUÇÃO AUTÔNOMA", "AUTÔNOMO"]:
            new_status_enum = MachineStatus.IN_USE_AUTONOMOUS
            category = "PRODUCING"

        # Refino pelo motivo enviado
        final_reason = event.reason or new_status_enum.value
        reason_upper = final_reason.upper()
        
        # 🚀 CORREÇÃO DA MANUTENÇÃO: 
        # Se a palavra 'FIM' estiver no motivo OU o sinal que chegou for explicitamente 'AVAILABLE'
        # Nós NÃO deixamos o refinador alterar o status de volta pra Manutenção ou Setup!
        is_end_of_process = "FIM" in reason_upper or "AVAILABLE" in sinal_recebido or "DISPONÍVEL" in sinal_recebido

        if not is_end_of_process:
            if "SETUP" in reason_upper or "PREPARAÇÃO" in reason_upper:
                new_status_enum = MachineStatus.SETUP
                category = "PLANNED_STOP"
            elif "MANUTENÇÃO" in reason_upper or "QUEBRA" in reason_upper:
                new_status_enum = MachineStatus.MAINTENANCE
                category = "MAINTENANCE"
            elif "AUTÔNOMA" in reason_upper:
                new_status_enum = MachineStatus.IN_USE_AUTONOMOUS
                category = "PRODUCING"

        # --- 3. FILTRO ANTI-LIXO (Evita logoff quebrar status de manutenção) ---
        if last_log_status in [MachineStatus.MAINTENANCE.value, MachineStatus.SETUP.value]:
            if final_reason and ("SAÍDA" in reason_upper or "LOGOFF" in reason_upper):
                return {"status": "ignored", "reason": "Ignored generic logout during specialized state"}

        # --- 4. TRAVA DE REDUNDÂNCIA ---
        if machine.status == new_status_enum.value:
            active_slice = await ProductionService.get_active_slice(db, machine.id)
            if active_slice and active_slice.category == category:
                
                current_reason = active_slice.reason or ""
                # Define o que é um motivo genérico (vazio)
                is_new_generic = final_reason in ["SEM MOTIVO", "Parada", "Status: Parada", "Status: STOPPED"]
                is_current_generic = current_reason in ["SEM MOTIVO", "Parada", "Status: Parada", "Status: STOPPED", ""]

                # O motivo mudou?
                if current_reason != final_reason:
                    
                    # ESCUDO: Se a máquina já tem um motivo real (Falta de Peça) e chega um ping genérico (SEM MOTIVO), ignora!
                    if is_new_generic and not is_current_generic:
                        return {"status": "ignored", "reason": "Ignorando motivo genérico sobrepondo motivo específico."}

                    # 1. Atualiza a fatia de tempo (Time Slice)
                    active_slice.reason = final_reason
                    db.add(active_slice)
                    
                    # 🚀 2. A CORREÇÃO: Atualiza o LOG para refletir na tabela do Frontend!
                    stmt_last_log = select(ProductionLog).where(
                        ProductionLog.machine_id == machine.id
                    ).order_by(desc(ProductionLog.timestamp)).limit(1)
                    
                    last_log = (await db.execute(stmt_last_log)).scalars().first()
                    
                    # Só altera se o log bater com o status atual (evita alterar logs antigos acidentalmente)
                    if last_log and last_log.new_status == new_status_enum.value:
                        last_log.reason = final_reason
                        db.add(last_log)

                    await db.commit()
                    return {"status": "mutated", "category": category, "new_machine_status": machine.status}
                
                return {"status": "ignored", "reason": "Status e Motivo idênticos ao atual."}

        # --- 5. SOBRESCRITA INTELIGENTE (Mudança de Motivo de Parada) ---
        is_currently_stopped = machine.status == MachineStatus.STOPPED.value
        wants_to_specify = new_status_enum in [MachineStatus.SETUP, MachineStatus.MAINTENANCE]
        
        if is_currently_stopped and wants_to_specify:
            active_slice = await ProductionService.get_active_slice(db, machine.id)
            # Permite mudar a história se fizer menos de 10 minutos
            if active_slice and (timestamp - active_slice.start_time).total_seconds() < 600:
                active_slice.category = category
                active_slice.reason = final_reason
                machine.status = new_status_enum.value
                
                db.add(active_slice)
                db.add(machine)
                
                # Atualiza o Log também
                stmt_last_log = select(ProductionLog).where(ProductionLog.machine_id == machine.id).order_by(desc(ProductionLog.timestamp)).limit(1)
                last_log = (await db.execute(stmt_last_log)).scalars().first()
                if last_log and last_log.new_status == MachineStatus.STOPPED.value:
                    last_log.new_status = new_status_enum.value
                    last_log.reason = final_reason
                    db.add(last_log)

                await db.commit()
                return {"status": "overwritten", "category": category, "new_machine_status": machine.status}

        # --- 6. TRANSIÇÃO NORMAL (Fecha a antiga, Abre a nova) ---
        await ProductionService.close_current_slice(db, machine.id, timestamp)
        
        sess_id = active_session.id if active_session else None
        ord_id = active_session.production_order_id if active_session else None
        
        await ProductionService.open_new_slice(
            db, 
            machine_id=machine.id, 
            category=category, 
            reason=final_reason,
            session_id=sess_id,
            order_id=ord_id
        )

        machine.status = new_status_enum.value
        db.add(machine)

        log = ProductionLog(
            machine_id=machine.id, 
            operator_id=user_id,      
            operator_badge=badge,     
            operator_name=user_name,  
            event_type=event.event_type, 
            new_status=new_status_enum.value,
            reason=final_reason, 
            timestamp=timestamp
        )
        db.add(log)
        await db.commit()
        
        return {"id": log.id, "status": "processed", "category": category, "new_machine_status": machine.status}

    @staticmethod
    async def update_current_slice_reason(db: AsyncSession, machine_id: int, new_reason: str, new_category: str = None):
        """Atualiza motivo e opcionalmente a categoria da fatia aberta."""
        active_slice = await ProductionService.get_active_slice(db, machine_id)
        if active_slice:
            active_slice.reason = new_reason
            if new_category:
                active_slice.category = new_category 
            db.add(active_slice)
            return True
        return False

    @staticmethod
    async def calculate_oee(db: AsyncSession, machine_id: int, start_date: datetime, end_date: datetime):
        """Calcula métricas, separa Pausa de Ocioso e gera Pareto."""
        query = select(ProductionTimeSlice).where(
            ProductionTimeSlice.machine_id == machine_id,
            ProductionTimeSlice.start_time >= start_date,
            ProductionTimeSlice.start_time <= end_date
        )
        slices = (await db.execute(query)).scalars().all()
        
        BLACKLIST_TERMS = [
            "STATUS:", "EM OPERAÇÃO", "RUNNING", "OPERAÇÃO", "IDLE", 
            "AVAILABLE", "DISPONÍVEL", "SISTEMA", "111", "21", "SETUP", "PREPARAÇÃO", "SAIDA", "SAÍDA",
            "EM USO", "IN_USE", "PARADA CURTA", 
            "FIM DE MANUTENÇÃO", "LIBERADA", "DESBLOQUEIO", "MÁQUINA LIBERADA", "MÁQUINA EM MANUTENÇÃO"
        ]
        
        run_sec, maint_sec, planned_sec, idle_sec, pause_sec, micro_sec = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        num_failures = 0
        reasons_duration_map = {}

        for s in slices:
            s_start = max(s.start_time, start_date)
            s_end = min(s.end_time or datetime.now(), end_date)
            duration = (s_end - s_start).total_seconds()
            if duration <= 1: continue

            reason_raw = (s.reason or "").strip()
            cat = (s.category or "").upper()
            reason_upper = reason_raw.upper()

            # 1. Manutenção
            if cat == "MAINTENANCE": 
                maint_sec += duration
                if duration > 300: num_failures += 1

            # 2. Setup
            elif cat == "PLANNED_STOP": 
                planned_sec += duration

            # 3. Produção
            elif cat == "PRODUCING":
                run_sec += duration

            # 4. Ociosidade (Card Cinza)
            elif cat == "IDLE" or "AVAILABLE" in reason_upper or "DISPONÍVEL" in reason_upper or "LIBERADA" in reason_upper:
                idle_sec += duration

            # 5. Paradas (Card Laranja) e Micro-paradas (Card Preto)
            elif cat == "UNPLANNED_STOP" or cat == "MICRO_STOP":
                 if cat == "MICRO_STOP" or duration < 300: 
                     micro_sec += duration
                 else:
                     pause_sec += duration 

            # 6. Pareto
            if reason_raw and not any(term in reason_upper for term in BLACKLIST_TERMS):
                clean_label = reason_raw.replace("Micro-parada: ", "").replace("Parada: ", "").replace("Status: ", "").strip()
                reasons_duration_map[clean_label] = reasons_duration_map.get(clean_label, 0.0) + duration

        total_sec = run_sec + maint_sec + planned_sec + idle_sec + pause_sec + micro_sec
        div_avail = total_sec - planned_sec 
        availability = (run_sec / div_avail * 100) if div_avail > 0 else 0.0

        return {
            "oee_percentage": round(availability, 1),
            "availability": round(availability, 1),
            "mtbf": round((run_sec / 3600) / num_failures, 1) if num_failures > 0 else round(run_sec / 3600, 1),
            "mttr": round((maint_sec / 3600) / num_failures, 1) if num_failures > 0 else 0.0,
            "reasons_map": reasons_duration_map,
            "metrics": {
                "producing_min": run_sec / 60,
                "maintenance_min": maint_sec / 60,
                "planned_stop_min": planned_sec / 60,
                "idle_min": idle_sec / 60,
                "pause_min": pause_sec / 60, 
                "micro_stop_min": micro_sec / 60,
                "total_min": total_sec / 60
            }
        }

    @staticmethod
    async def consolidate_machine_metrics(db: AsyncSession, target_date: date):
        """Salva a performance diária das máquinas no histórico."""
        from sqlalchemy import select
        from datetime import datetime, time as dt_time

        print(f"\n--- [DEBUG CONSOLIDATE] Iniciando processamento de Máquinas para: {target_date} ---")

        start_of_day = datetime.combine(target_date, dt_time.min)
        end_of_day = datetime.combine(target_date, dt_time.max)
        
        machines = (await db.execute(select(Machine))).scalars().all()
        count = 0
        
        for machine in machines:
            try:
                res = await ProductionService.calculate_oee(db, machine.id, start_of_day, end_of_day)

                active_time = res["metrics"]["producing_min"] + res["metrics"]["maintenance_min"] + res["metrics"]["idle_min"] + res["metrics"]["pause_min"]
                if active_time == 0:
                    continue

                q_exist = select(MachineDailyMetric).where(
                    MachineDailyMetric.date == target_date, 
                    MachineDailyMetric.machine_id == machine.id
                )
                metric = (await db.execute(q_exist)).scalars().first()
                
                if not metric:
                    org_id = getattr(machine, 'organization_id', 1) or 1
                    metric = MachineDailyMetric(date=target_date, machine_id=machine.id, organization_id=org_id)
                    db.add(metric)
                
                metric.running_hours = round(res["metrics"]["producing_min"] / 60, 2)
                metric.maintenance_hours = round(res["metrics"]["maintenance_min"] / 60, 2)
                metric.planned_stop_hours = round(res["metrics"]["planned_stop_min"] / 60, 2)
                metric.idle_hours = round(res["metrics"]["idle_min"] / 60, 2)
                metric.pause_hours = round(res["metrics"]["pause_min"] / 60, 2) # Garantido
                metric.micro_stop_hours = round(res["metrics"]["micro_stop_min"] / 60, 2)
                metric.total_hours = round(res["metrics"]["total_min"] / 60, 2)
                metric.availability = res["availability"]
                metric.mtbf = res["mtbf"]
                metric.mttr = res["mttr"]
                
                metric.top_reasons_snapshot = [
                    {"label": k, "hours": round(v / 3600, 3)} 
                    for k, v in sorted(res["reasons_map"].items(), key=lambda x: x[1], reverse=True)[:5]
                ]
                
                metric.closed_at = datetime.now()
                count += 1
            except Exception as e:
                print(f"Erro na consolidação da máquina {machine.id}: {e}")
                continue
            
        await db.commit()
        return count

    @staticmethod
    async def consolidate_daily_metrics(db: AsyncSession, target_date: date):
        """Fechamento Diário: Calcula métricas baseadas em LOGS dos operadores e salva no banco."""
        print(f"🔄 [CRON] Iniciando Fechamento Diário (Operadores) para: {target_date}")
        
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        q_active_users = select(ProductionLog.operator_id).where(
            ProductionLog.timestamp >= start_of_day,
            ProductionLog.timestamp <= end_of_day,
            ProductionLog.operator_id != None
        ).distinct()
        
        active_user_ids = (await db.execute(q_active_users)).scalars().all()
        
        count = 0
        for user_id in active_user_ids:
            q_logs = select(ProductionLog).where(
                ProductionLog.operator_id == user_id,
                ProductionLog.timestamp >= start_of_day,
                ProductionLog.timestamp <= end_of_day
            ).order_by(ProductionLog.machine_id, ProductionLog.timestamp)
            
            user_logs = (await db.execute(q_logs)).scalars().all()
            
            prod_sec = 0.0
            unprod_sec = 0.0
            reasons_map = {}
            
            for log in user_logs:
                q_next = select(ProductionLog).where(
                    ProductionLog.machine_id == log.machine_id,
                    ProductionLog.timestamp > log.timestamp
                ).order_by(ProductionLog.timestamp.asc()).limit(1)
                next_log = (await db.execute(q_next)).scalars().first()
                
                limit_time = end_of_day
                if target_date == date.today():
                    limit_time = datetime.now()
                
                next_time = next_log.timestamp if next_log else limit_time
                if next_time > end_of_day: next_time = end_of_day
                
                duration = (next_time - log.timestamp).total_seconds()
                duration = max(0.0, duration) 

                st = (log.new_status or "").upper()
                reason = (log.reason or "").upper()
                
                is_available = st in ["AVAILABLE", "IDLE", "DISPONÍVEL", "DISPONIVEL"]
                is_running = st in ["RUNNING", "EM OPERAÇÃO", "EM USO", "PRODUCING", "IN_USE"]
                
                has_setup_keyword = "SETUP" in st or "SETUP" in reason or "PREPARAÇÃO" in reason
                is_setup = has_setup_keyword and not is_available and not is_running
                
                if is_running or is_setup:
                    prod_sec += duration
                else:
                    unprod_sec += duration
                    if duration > 60:
                        lbl = log.reason or st or "Parada genérica"
                        if lbl not in reasons_map: reasons_map[lbl] = 0
                        reasons_map[lbl] += 1

            total_sec = prod_sec + unprod_sec
            efficiency = (prod_sec / total_sec * 100) if total_sec > 0 else 0.0
            
            sorted_reasons = sorted(reasons_map.items(), key=lambda x: x[1], reverse=True)[:3]
            top_reasons_list = [{"label": k, "count": v} for k, v in sorted_reasons]

            q_exists = select(EmployeeDailyMetric).where(
                EmployeeDailyMetric.date == target_date,
                EmployeeDailyMetric.user_id == user_id
            )
            metric_entry = (await db.execute(q_exists)).scalars().first()
            
            if not metric_entry:
                metric_entry = EmployeeDailyMetric(
                    date=target_date, 
                    user_id=user_id, 
                    organization_id=1 
                )
                db.add(metric_entry)
            
            metric_entry.total_hours = round(total_sec / 3600, 2)
            metric_entry.productive_hours = round(prod_sec / 3600, 2)
            metric_entry.unproductive_hours = round(unprod_sec / 3600, 2)
            metric_entry.efficiency = round(efficiency, 1)
            metric_entry.top_reasons_snapshot = top_reasons_list
            metric_entry.closed_at = datetime.now()
            
            count += 1
        
        await db.commit()
        print(f"✅ [CRON] Fechamento de Operadores para {target_date} concluído. {count} processados.")
        return count