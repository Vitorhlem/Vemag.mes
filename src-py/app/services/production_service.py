from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any

# Models
from app.models.production_model import VehicleDailyMetric, EmployeeDailyMetric, ProductionLog, ProductionOrder, ProductionSession, ProductionTimeSlice
from app.models.vehicle_model import Vehicle, VehicleStatus
from app.models.user_model import User

# Schemas
from app.schemas.production_schema import ProductionEventCreate

class ProductionService:
    
    @staticmethod
    async def get_active_slice(db: AsyncSession, vehicle_id: int) -> Optional[ProductionTimeSlice]:
        """Busca a fatia de tempo que está aberta (sem end_time) para a máquina."""
        query = select(ProductionTimeSlice).where(
            ProductionTimeSlice.vehicle_id == vehicle_id,
            ProductionTimeSlice.end_time == None
        ).order_by(desc(ProductionTimeSlice.start_time))
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def close_current_slice(db: AsyncSession, vehicle_id: int, end_time: datetime = None):
        """Fecha a fatia atual aplicando a regra de micro-parada APENAS para pausas comuns."""
        if not end_time: end_time = datetime.now()
        current_slice = await ProductionService.get_active_slice(db, vehicle_id)
        
        if current_slice:
            current_slice.end_time = end_time
            delta = (end_time - current_slice.start_time).total_seconds()
            current_slice.duration_seconds = int(max(0, delta))
            
            # --- NOVA REGRA RESTRITA ---
            # Só vira MICRO_STOP se a categoria original for UNPLANNED_STOP ou IDLE
            # Se for PRODUCING, MAINTENANCE ou PLANNED_STOP (Setup), não mexe!
            target_categories = ["UNPLANNED_STOP", "IDLE", "AVAILABLE"]
            
            if current_slice.category in target_categories and 2 < delta < 300:
                current_slice.category = "MICRO_STOP"
                current_slice.reason = f"Micro-parada: {current_slice.reason or 'Parada curta'}"
            
            db.add(current_slice)
            await db.commit()
            return current_slice
        return None

    @staticmethod
    async def consolidate_machine_metrics(db: AsyncSession, target_date: date):
        """
        Calcula e salva o desempenho das MÁQUINAS consolidando fatias de tempo.
        Persiste OEE, MTBF, MTTR e o Pareto de motivos no histórico diário.
        """
        from app.models.vehicle_model import Vehicle
        from app.models.production_model import ProductionTimeSlice, VehicleDailyMetric
        from sqlalchemy import select, or_
        from datetime import datetime, time as dt_time

        print(f"\n--- [DEBUG CONSOLIDATE] Iniciando processamento para a data: {target_date} ---")

        start_of_day = datetime.combine(target_date, dt_time.min)
        end_of_day = datetime.combine(target_date, dt_time.max)
        
        # 1. Busca todas as máquinas cadastradas
        machines = (await db.execute(select(Vehicle))).scalars().all()
        print(f"[DEBUG CONSOLIDATE] {len(machines)} máquinas encontradas para processamento.")
        
        count = 0
        for machine in machines:
            print(f"  > Processando Máquina ID: {machine.id} ({machine.brand} {machine.model})")
            
            try:
                # 2. Utiliza o motor de cálculo unificado (Garante MTBF/MTTR e paridade com OEE)
                # Esta função deve retornar: availability, mtbf, mttr, reasons_map e metrics
                res = await ProductionService.calculate_oee(db, machine.id, start_of_day, end_of_day)

                # 3. Filtro de atividade: se a máquina não teve nenhum movimento no dia, ignora a criação do registro
                active_time = res["metrics"]["producing_min"] + res["metrics"]["maintenance_min"] + res["metrics"]["idle_min"]
                if active_time == 0:
                    print(f"    - Máquina sem atividade registrada neste dia. Pulando.")
                    continue

                # 4. Persistência (Upsert): Busca registro existente ou cria um novo
                q_exist = select(VehicleDailyMetric).where(
                    VehicleDailyMetric.date == target_date, 
                    VehicleDailyMetric.vehicle_id == machine.id
                )
                metric = (await db.execute(q_exist)).scalars().first()
                
                if not metric:
                    print(f"    - Criando novo registro de métrica diária...")
                    # Tenta pegar a organização da máquina, se não existir usa 1 como padrão
                    org_id = getattr(machine, 'organization_id', 1) or 1
                    metric = VehicleDailyMetric(
                        date=target_date, 
                        vehicle_id=machine.id, 
                        organization_id=org_id
                    )
                    db.add(metric)
                
                # 5. Atribuição dos indicadores calculados
                print(f"    - Atribuindo indicadores: OEE={res['availability']}% | MTBF={res['mtbf']}h | MTTR={res['mttr']}h")
                
                metric.running_hours = round(res["metrics"]["producing_min"] / 60, 2)
                metric.maintenance_hours = round(res["metrics"]["maintenance_min"] / 60, 2)
                metric.planned_stop_hours = round(res["metrics"]["planned_stop_min"] / 60, 2)
                metric.idle_hours = round(res["metrics"]["idle_min"] / 60, 2)
                metric.micro_stop_hours = round(res["metrics"]["micro_stop_min"] / 60, 2)
                metric.total_hours = round(res["metrics"]["total_min"] / 60, 2)
                
                metric.availability = res["availability"]
                metric.mtbf = res["mtbf"]
                metric.mttr = res["mttr"]
                
                # 6. Formatação do Top Ofensores (Pareto de Tempo em Horas)
                # Consome o 'reasons_map' devolvido pelo calculate_oee
                metric.top_reasons_snapshot = [
                {"label": k, "hours": round(v / 3600, 3)} 
                for k, v in sorted(res["reasons_map"].items(), key=lambda x: x[1], reverse=True)[:5]
                ]
                
                metric.closed_at = datetime.now()
                count += 1

            except Exception as machine_error:
                print(f"    - ❌ Erro ao processar Máquina {machine.id}: {str(machine_error)}")
                continue
            
        # 7. Finaliza a transação
        try:
            await db.commit()
            print(f"--- [DEBUG CONSOLIDATE] Finalizado. {count} máquinas atualizadas. ---\n")
        except Exception as commit_error:
            print(f"❌ [ERRO CRÍTICO] Falha ao realizar commit no banco: {str(commit_error)}")
            await db.rollback()
            raise commit_error

        return count
    @staticmethod
    async def open_new_slice(
        db: AsyncSession, 
        vehicle_id: int, 
        category: str, 
        reason: Optional[str] = None,
        session_id: Optional[int] = None,
        order_id: Optional[int] = None
    ) -> ProductionTimeSlice:
        """Abre uma nova fatia de tempo. (REMOVIDO COMMIT PREMATURO)"""
        is_productive = category == "PRODUCING"
        
        new_slice = ProductionTimeSlice(
            vehicle_id=vehicle_id,
            start_time=datetime.now(),
            category=category,
            reason=reason,
            is_productive=is_productive,
            session_id=session_id,
            order_id=order_id
        )
        db.add(new_slice)
        await db.flush() # Usa flush em vez de commit para manter a transação do handle_event
        return new_slice


    @staticmethod
    async def consolidate_daily_metrics(db: AsyncSession, target_date: date):
        """
        Executa o Fechamento Diário: Calcula métricas baseadas em LOGS e salva no banco.
        Pode ser rodado várias vezes para o mesmo dia (atualiza os dados se já existirem).
        """
        print(f"🔄 [CRON] Iniciando Fechamento Diário para: {target_date}")
        
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        # 1. Busca todos os usuários (da organização 1 por padrão ou itera por orgs)
        # Para simplificar, vamos pegar todos os usuários que tiveram logs no dia
        q_active_users = select(ProductionLog.operator_id).where(
            ProductionLog.timestamp >= start_of_day,
            ProductionLog.timestamp <= end_of_day,
            ProductionLog.operator_id != None
        ).distinct()
        
        active_user_ids = (await db.execute(q_active_users)).scalars().all()
        
        count = 0
        for user_id in active_user_ids:
            # 2. Reutiliza a Lógica de Logs (Aprovada) para calcular este usuário
            q_logs = select(ProductionLog).where(
                ProductionLog.operator_id == user_id,
                ProductionLog.timestamp >= start_of_day,
                ProductionLog.timestamp <= end_of_day
            ).order_by(ProductionLog.vehicle_id, ProductionLog.timestamp)
            
            user_logs = (await db.execute(q_logs)).scalars().all()
            
            prod_sec = 0.0
            unprod_sec = 0.0
            reasons_map = {}
            
            # Algoritmo de Reconstrução de Linha do Tempo
            for log in user_logs:
                q_next = select(ProductionLog).where(
                    ProductionLog.vehicle_id == log.vehicle_id,
                    ProductionLog.timestamp > log.timestamp
                ).order_by(ProductionLog.timestamp.asc()).limit(1)
                next_log = (await db.execute(q_next)).scalars().first()
                
                # Se não tem próximo log no dia, assume fim do dia ou agora (se for hoje)
                limit_time = end_of_day
                if target_date == date.today():
                    limit_time = datetime.now()
                
                next_time = next_log.timestamp if next_log else limit_time
                
                # Truncar para o dia alvo (caso o próximo log seja amanhã)
                if next_time > end_of_day: next_time = end_of_day
                
                duration = (next_time - log.timestamp).total_seconds()
                duration = max(0.0, duration) # Proteção

                st = (log.new_status or "").upper()
                reason = (log.reason or "").upper()
                
                # Definição de Estados
                is_available = st in ["AVAILABLE", "IDLE", "DISPONÍVEL", "DISPONIVEL"]
                is_running = st in ["RUNNING", "EM OPERAÇÃO", "EM USO", "PRODUCING", "IN_USE"]
                
                # CORREÇÃO: Setup só é verdadeiro se NÃO for 'Available'
                # Isso impede que "Fim de Setup" (que contém a palavra Setup) conte como tempo produtivo
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
            
            # Top 3 Motivos
            sorted_reasons = sorted(reasons_map.items(), key=lambda x: x[1], reverse=True)[:3]
            top_reasons_list = [{"label": k, "count": v} for k, v in sorted_reasons]

            # 3. Salvar/Atualizar na Tabela de Métricas
            q_exists = select(EmployeeDailyMetric).where(
                EmployeeDailyMetric.date == target_date,
                EmployeeDailyMetric.user_id == user_id
            )
            metric_entry = (await db.execute(q_exists)).scalars().first()
            
            if not metric_entry:
                metric_entry = EmployeeDailyMetric(
                    date=target_date, 
                    user_id=user_id, 
                    organization_id=1 # Fixo por enquanto, ou pegar do User
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
        print(f"✅ [CRON] Fechamento de {target_date} concluído. {count} registros processados.")
        return count

    @staticmethod
    async def handle_event(db: AsyncSession, event: ProductionEventCreate) -> Dict[str, Any]:
        timestamp = datetime.now()
        machine = await db.get(Vehicle, event.machine_id)
        if not machine: raise ValueError("Machine not found")

        sinal_recebido = str(event.new_status).upper() 
        
        # --- 🔍 NOVA LÓGICA: IDENTIFICAÇÃO DO OPERADOR REAL ---
        badge = str(event.operator_badge or "").strip()
        user_id = None
        user_name = "Sistema"

        # Se o sinal vem do Hardware (PLC), buscamos quem é o dono da sessão ativa
        if badge == "ESP32_HARDWARE":
            # Busca a sessão que está aberta para esta máquina agora
            stmt_session = select(ProductionSession).where(
                ProductionSession.vehicle_id == machine.id,
                ProductionSession.end_time == None
            ).order_by(desc(ProductionSession.start_time)).limit(1)
            
            result_sess = await db.execute(stmt_session)
            active_session = result_sess.scalars().first()

            if active_session:
                # Se achamos o operador logado, usamos os dados dele no log
                user_q = await db.execute(select(User).where(User.id == active_session.user_id))
                user = user_q.scalars().first()
                if user:
                    user_id = user.id
                    user_name = user.full_name
                    badge = user.employee_id # Substitui o texto "Hardware" pelo crachá real
            else:
                user_name = "Hardware PLC" # Só mostra se realmente não houver ninguém logado
        
        elif badge:
            # Lógica normal para eventos manuais (Tablet)
            from sqlalchemy import or_
            user_q = await db.execute(select(User).where(or_(User.employee_id == badge, User.email == badge)))
            user = user_q.scalars().first()
            if user:
                user_id = user.id
                user_name = user.full_name

        # Busca o último log para decisões inteligentes
        stmt_last = select(ProductionLog).where(ProductionLog.vehicle_id == machine.id).order_by(ProductionLog.timestamp.desc()).limit(1)
        last_log = (await db.execute(stmt_last)).scalars().first()
        last_log_status = last_log.new_status if last_log else machine.status

        # ---------------------------------------------------------
        # 1. LÓGICA DE MÁQUINA DE ESTADOS
        # ---------------------------------------------------------
        new_status_enum = VehicleStatus.STOPPED 
        category = "UNPLANNED_STOP" 

        # Cenario A: Produção
        if sinal_recebido in ["1", "RUNNING", "EM OPERAÇÃO", "PRODUCING"]:
            if last_log_status == VehicleStatus.IN_USE_AUTONOMOUS and sinal_recebido == "1":
                new_status_enum = VehicleStatus.IN_USE_AUTONOMOUS
                category = "PRODUCING"
            else:
                new_status_enum = VehicleStatus.IN_USE
                category = "PRODUCING"

        # Cenario B: Parada
        elif sinal_recebido in ["0", "STOPPED", "PAUSADA", "PARADA"]:
            new_status_enum = VehicleStatus.STOPPED
            category = "UNPLANNED_STOP"

        # Cenario C: Overrides (Setup, Manutenção, Autônomo)
        elif sinal_recebido == "SETUP":
            new_status_enum = VehicleStatus.SETUP
            category = "PLANNED_STOP"
        elif sinal_recebido in ["MAINTENANCE", "EM MANUTENÇÃO"]:
            new_status_enum = VehicleStatus.MAINTENANCE
            category = "MAINTENANCE"
        elif sinal_recebido in ["IN_USE_AUTONOMOUS", "PRODUÇÃO AUTÔNOMA"]:
            new_status_enum = VehicleStatus.IN_USE_AUTONOMOUS
            category = "PRODUCING"
        elif sinal_recebido in ["OCIOSO", "OCIOSIDADE", "AVAILABLE", "DISPONIVEL", "LIBERADA"]:
            new_status_enum = VehicleStatus.AVAILABLE 
            category = "IDLE"
            if not event.reason or event.reason == "null":
                event.reason = "Máquina Disponível"

        # ---------------------------------------------------------
        # 2. INFERÊNCIA DE STATUS PELO MOTIVO
        # ---------------------------------------------------------
        final_reason = event.reason
        if final_reason:
            reason_upper = final_reason.upper()
            is_end_of_process = "FIM" in reason_upper or "AVAILABLE" in str(event.new_status).upper()

            if not is_end_of_process:
                if "SETUP" in reason_upper or "PREPARAÇÃO" in reason_upper:
                    new_status_enum = VehicleStatus.SETUP
                    category = "PLANNED_STOP"
                elif "MANUTENÇÃO" in reason_upper or "QUEBRA" in reason_upper or "CONSERTO" in reason_upper:
                    new_status_enum = VehicleStatus.MAINTENANCE
                    category = "MAINTENANCE"
                elif "AUTÔNOMA" in reason_upper:
                    new_status_enum = VehicleStatus.IN_USE_AUTONOMOUS
                    category = "PRODUCING"

        if new_status_enum == VehicleStatus.STOPPED and not final_reason:
            final_reason = "SEM MOTIVO"
        elif not final_reason:
            final_reason = new_status_enum.value

        # ---------------------------------------------------------
        # 🚨 FILTRO ANTI-LIXO
        # ---------------------------------------------------------
        if last_log_status in [VehicleStatus.MAINTENANCE, VehicleStatus.SETUP]:
            if final_reason and ("SAÍDA" in final_reason.upper() or "LOGOFF" in final_reason.upper()):
                return {"status": "ignored", "reason": "Ignored generic logout during specialized state"}

        # ---------------------------------------------------------
        # 3. LÓGICA DE SOBRESCRITA
        # ---------------------------------------------------------
        should_overwrite = False
        is_last_stopped = last_log_status in ["STOPPED", "PAUSADA", "Parada", "0"]
        
        if machine.status == new_status_enum.value and final_reason != "SEM MOTIVO":
            should_overwrite = True
        elif is_last_stopped and new_status_enum in [VehicleStatus.SETUP, VehicleStatus.MAINTENANCE, VehicleStatus.IN_USE_AUTONOMOUS]:
            should_overwrite = True
        elif last_log_status == new_status_enum.value and new_status_enum in [VehicleStatus.MAINTENANCE, VehicleStatus.SETUP]:
             should_overwrite = True

        if should_overwrite and last_log:
             allow_update = (
                 last_log.reason in ["SEM MOTIVO", "Parada", "STOPPED"] or 
                 "TROCA DE TURNO" in str(last_log.reason).upper() or
                 new_status_enum == VehicleStatus.MAINTENANCE
             )

             if allow_update:
                 await ProductionService.update_current_slice_reason(db, machine.id, final_reason, new_category=category)
                 machine.status = new_status_enum.value
                 last_log.reason = final_reason
                 last_log.new_status = new_status_enum.value 
                 # Atualiza dados do operador se necessário
                 last_log.operator_id = user_id
                 last_log.operator_badge = badge
                 last_log.operator_name = user_name
                 
                 db.add(last_log)
                 await db.commit()
                 return {"status": "updated", "category": category, "new_machine_status": machine.status}

        # ---------------------------------------------------------
        # 4. TRAVA DE REDUNDÂNCIA
        # ---------------------------------------------------------
        if last_log_status == new_status_enum.value:
            if last_log and last_log.reason == final_reason:
                return {"status": "ignored", "reason": "Redundant status and reason"}

        # ---------------------------------------------------------
        # 5. NOVO REGISTRO (LOG)
        # ---------------------------------------------------------
        machine.status = new_status_enum.value
        await ProductionService.close_current_slice(db, machine.id, timestamp)
        await ProductionService.open_new_slice(db, vehicle_id=machine.id, category=category, reason=final_reason)

        # ✅ CORREÇÃO FINAL: Usa os campos separados
        log = ProductionLog(
            vehicle_id=machine.id, 
            operator_id=user_id,      # ID Numérico (ou None)
            operator_badge=badge,     # String (ex: "ESP32_HARDWARE")
            operator_name=user_name,  # String
            event_type=event.event_type, 
            new_status=new_status_enum.value,
            reason=final_reason, 
            timestamp=timestamp
        )
        db.add(log)
        await db.commit()
        
        return {"id": log.id, "status": "processed", "category": category, "new_machine_status": machine.status}
    @staticmethod
    async def update_current_slice_reason(db: AsyncSession, vehicle_id: int, new_reason: str, new_category: str = None):
        """
        Atualiza motivo e opcionalmente a categoria da fatia aberta.
        """
        from app.models.production_model import ProductionTimeSlice
        from sqlalchemy import select

        stmt = select(ProductionTimeSlice).where(
            ProductionTimeSlice.vehicle_id == vehicle_id,
            ProductionTimeSlice.end_time == None
        ).order_by(ProductionTimeSlice.start_time.desc()).limit(1)

        result = await db.execute(stmt)
        active_slice = result.scalars().first()

        if active_slice:
            active_slice.reason = new_reason
            if new_category:
                active_slice.category = new_category # ✅ Atualiza categoria (ex: vira PLANNED_STOP)
            db.add(active_slice)
            print(f"✅ [MES] Fatia {active_slice.id} atualizada: {new_reason} [{active_slice.category}]")
            return True
        
        return False
    
    @staticmethod
    async def calculate_oee(db: AsyncSession, vehicle_id: int, start_date: datetime, end_date: datetime):
        """Calcula métricas e gera Pareto livre de Whitelist."""
        query = select(ProductionTimeSlice).where(
            ProductionTimeSlice.vehicle_id == vehicle_id,
            ProductionTimeSlice.start_time >= start_date,
            ProductionTimeSlice.start_time <= end_date
        )
        slices = (await db.execute(query)).scalars().all()
        
        # ✅ CORREÇÃO: "SETUP" e "PREPARAÇÃO" adicionados à lista negra
        BLACKLIST_TERMS = [
            "STATUS:", "EM OPERAÇÃO", "RUNNING", "OPERAÇÃO", "IDLE", 
            "AVAILABLE", "DISPONÍVEL", "SISTEMA", "111", "21", "SETUP", "PREPARAÇÃO", "SAIDA", "SAÍDA"
        ]
        run_sec, maint_sec, planned_sec, idle_sec, micro_sec = 0.0, 0.0, 0.0, 0.0, 0.0
        num_failures = 0
        reasons_duration_map = {}

        for s in slices:
            s_start = max(s.start_time, start_date)
            s_end = min(s.end_time or datetime.now(), end_date)
            duration = (s_end - s_start).total_seconds()
            if duration <= 1: continue

            reason_raw = (s.reason or "").strip()
            cat = (s.category or "").upper()
            reason_upper = (s.reason or "").upper()

            # 1. KPIs (Acúmulo de tempos)
            if cat == "MAINTENANCE": 
                maint_sec += duration
                if duration > 300: num_failures += 1

            # 2. Setup (Explícito pelo Status/Categoria PLANNED_STOP que definimos no handle_event)
            elif cat == "PLANNED_STOP": 
                planned_sec += duration

            # 3. Produção (Humana ou Autônoma)
            elif cat == "PRODUCING":
                run_sec += duration

            # 4. Paradas Não Planejadas
            elif cat == "UNPLANNED_STOP":
                 # Regra de 5 minutos
                 if duration < 300: 
                     micro_sec += duration
                 else:
                     # Se for "SEM MOTIVO", conta como IDLE (Cinza), senão PAUSE (Laranja)
                     if "SEM MOTIVO" in reason_upper:
                         idle_sec += duration 
                     else:
                         # Aqui entraria parada por falta de peça, etc.
                         # Você pode decidir se isso impacta Disponibilidade (Pause) ou não.
                         # Geralmente paradas operacionais vão para Pause.
                         # Se quiser separar OCIOSO explícito, adicione elif cat == "IDLE"
                         idle_sec += duration # Assumindo parada operacional longa como perda

            # 5. Ocioso / Disponível / Shift Change Frio
            elif cat == "IDLE":
                idle_sec += duration
            
            # Caso micro-stop já tenha sido processado no close_slice
            elif cat == "MICRO_STOP":
                micro_sec += duration

            # 2. PARETO (Gráfico de Ofensores)
            # Só adiciona se não for mensagem de sistema
            if reason_raw and not any(term in reason_upper for term in BLACKLIST_TERMS):
                # Limpa prefixos para o gráfico ficar limpo
                clean_label = reason_raw.replace("Parada: ", "").replace("Micro-parada: ", "").replace("Status: ", "").strip()
                reasons_duration_map[clean_label] = reasons_duration_map.get(clean_label, 0.0) + duration

        total_sec = run_sec + maint_sec + planned_sec + idle_sec + micro_sec
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
                "micro_stop_min": micro_sec / 60,
                "total_min": total_sec / 60
            }
        }