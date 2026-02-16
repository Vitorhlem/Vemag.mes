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
        """Fecha a fatia de tempo atual, calculando a duração."""
        if not end_time:
            end_time = datetime.now()
            
        current_slice = await ProductionService.get_active_slice(db, vehicle_id)
        
        if current_slice:
            current_slice.end_time = end_time
            # Calcula duração em segundos
            delta = (end_time - current_slice.start_time).total_seconds()
            current_slice.duration_seconds = int(max(0, delta))
            db.add(current_slice)
            await db.commit() # Commit parcial para garantir integridade
            return current_slice
        return None

    @staticmethod
    async def consolidate_machine_metrics(db: AsyncSession, target_date: date):
        """
        Calcula e salva o desempenho das MÁQUINAS consolidando fatias de tempo.
        Acumula HORAS por motivo de parada (Pareto de Tempo).
        """
        from app.models.vehicle_model import Vehicle
        from app.models.production_model import ProductionTimeSlice, VehicleDailyMetric
        from sqlalchemy import select, or_
        from datetime import datetime, time as dt_time

        # Termos técnicos que não devem ir para o gráfico de motivos reais
        BLACKLIST = ["STATUS:", "DISPONÍVEL", "EM USO", "RUNNING", "IDLE", "AVAILABLE", "SISTEMA", "OFFLINE", "PARADA", "EM OPERAÇÃO"]

        start_of_day = datetime.combine(target_date, dt_time.min)
        end_of_day = datetime.combine(target_date, dt_time.max)
        
        machines = (await db.execute(select(Vehicle))).scalars().all()
        
        count = 0
        for machine in machines:
            q_slices = select(ProductionTimeSlice).where(
                ProductionTimeSlice.vehicle_id == machine.id,
                ProductionTimeSlice.start_time <= end_of_day,
                or_(ProductionTimeSlice.end_time >= start_of_day, ProductionTimeSlice.end_time == None)
            )
            slices = (await db.execute(q_slices)).scalars().all()
            
            run_sec, maint_sec, planned_sec, idle_sec = 0.0, 0.0, 0.0, 0.0
            reasons_duration_map = {} 

            for s in slices:
                # 1. Definição imediata da variável para evitar NameError
                reason_raw = (s.reason or "").strip()
                
                # 2. Recorte do tempo para o dia alvo
                s_start = max(s.start_time, start_of_day)
                s_end = min(s.end_time or datetime.now(), end_of_day)
                duration = (s_end - s_start).total_seconds()
                
                if duration <= 2: continue # Ignora oscilações menores que 2s
                
                cat = (s.category or "").upper()
                
                # 3. Classificação e Acúmulo
                if cat == "PRODUCING":
                    run_sec += duration
                elif cat == "MAINTENANCE":
                    maint_sec += duration
                    # Acumula tempo de manutenção no Pareto
                    if reason_raw:
                        reasons_duration_map[reason_raw] = reasons_duration_map.get(reason_raw, 0.0) + duration
                elif cat == "PLANNED_STOP":
                    planned_sec += duration
                    # Setup também entra no Pareto como ofensor de tempo planejado
                    if "SETUP" in reason_raw.upper() or "PREPARAÇÃO" in reason_raw.upper():
                        reasons_duration_map[reason_raw] = reasons_duration_map.get(reason_raw, 0.0) + duration
                else:
                    idle_sec += duration
                    # Paradas não planejadas (Onde entram os motivos do SAP)
                    if reason_raw and not any(x in reason_raw.upper() for x in BLACKLIST):
                        clean_lbl = reason_raw.replace("Status: ", "").replace("Parada: ", "").strip()
                        reasons_duration_map[clean_lbl] = reasons_duration_map.get(clean_lbl, 0.0) + duration

            total_sec = run_sec + maint_sec + planned_sec + idle_sec
            if total_sec == 0: continue

            # 4. Cálculo de Disponibilidade Real (MES Standard)
            # Disponibilidade = Tempo Rodando / (Tempo Total - Paradas Planejadas)
            # Obs: Setup é planejado, mas aqui tratamos como 'indisponibilidade' para o OEE
            div_avail = total_sec - planned_sec
            availability = (run_sec / div_avail * 100) if div_avail > 0 else 0.0
            
            # 5. Formatação do Top Ofensores (Convertendo Segundos -> Horas)
            # Usamos o campo 'hours' para o front-end ler
            top_reasons = [
                {"label": k, "hours": round(v / 3600, 3)} 
                for k, v in sorted(reasons_duration_map.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
        for machine in machines:
            # Chama o calculate_oee para este dia específico para pegar o valor idêntico
            res = await ProductionService.calculate_oee(db, machine.id, start_of_day, end_of_day)

            # 6. Persistência
            q_exist = select(VehicleDailyMetric).where(
                VehicleDailyMetric.date == target_date, 
                VehicleDailyMetric.vehicle_id == machine.id
            )
            metric = (await db.execute(q_exist)).scalars().first()
            
            if not metric:
                metric = VehicleDailyMetric(date=target_date, vehicle_id=machine.id, organization_id=1)
                db.add(metric)
            
            metric.running_hours = round(res["metrics"]["producing_min"] / 60, 2)
            metric.maintenance_hours = round(maint_sec / 3600, 2)
            metric.planned_stop_hours = round(res["metrics"]["planned_stop_min"] / 60, 2)
            metric.idle_hours = round(idle_sec / 3600, 2)
            metric.total_hours = round(total_sec / 3600, 2)
            metric.availability = res["availability"] # Valor idêntico ao gráfico OEE
            metric.top_reasons_snapshot = top_reasons 
            metric.closed_at = datetime.now()
            count += 1
            
        await db.commit()
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

        # 1. Busca Sessão e Ordem
        q_session = select(ProductionSession).where(
            ProductionSession.vehicle_id == machine.id,
            ProductionSession.end_time == None
        )
        session = (await db.execute(q_session)).scalars().first()
        order = await db.get(ProductionOrder, session.production_order_id) if session and session.production_order_id else None

        # 2. Identificação do Operador
        user_id_str = str(event.operator_badge)
        from sqlalchemy import or_
        q_user = select(User).where(or_(User.employee_id == user_id_str, User.email == user_id_str))
        user = (await db.execute(q_user)).scalars().first()
        if user: user_id_str = str(user.id)

        # 3. MAPEAMENTO MES PROFISSIONAL
        # Setup vai para PLANNED_STOP (Parada Planejada)
        status_map = {
            "EM OPERAÇÃO": "PRODUCING", "RUNNING": "PRODUCING",
            "MANUTENÇÃO": "MAINTENANCE", 
            "SETUP": "PLANNED_STOP", # O tempo de Setup cai aqui
            "PARADA": "UNPLANNED_STOP", "STOPPED": "UNPLANNED_STOP"
        }
        
        new_status_upper = (event.new_status or "").upper()
        category = status_map.get(new_status_upper, "IDLE")
        final_reason = event.reason if event.reason else event.new_status

        # 4. Gestão de fatias de tempo
        await ProductionService.close_current_slice(db, machine.id, timestamp)
        await ProductionService.open_new_slice(
            db, 
            vehicle_id=machine.id, 
            category=category, 
            reason=final_reason,
            session_id=session.id if session else None,
            order_id=order.id if order else None
        )

        # 5. Log de Auditoria
        log = ProductionLog(
            vehicle_id=machine.id, operator_id=user_id_str,
            event_type=event.event_type, new_status=event.new_status,
            reason=final_reason, timestamp=timestamp
        )
        db.add(log)

        # 6. ATUALIZAÇÃO DO STATUS VISUAL (DASHBOARD)
        # Mesmo sendo categoria "PLANNED_STOP", visualmente mostramos "Em manutenção" (Vermelho)
        if new_status_upper == "SETUP":
            machine.status = "Em manutenção"
        elif category == "PRODUCING":
            machine.status = "Em uso"
        elif category == "UNPLANNED_STOP":
            machine.status = "Parada"
        else:
            machine.status = "Disponível"

        await db.commit()
        return {"id": log.id, "status": "processed"}
    @staticmethod
    async def calculate_oee(db: AsyncSession, vehicle_id: int, start_date: datetime, end_date: datetime):
        """
        Calcula OEE baseado na lógica robusta de classificação de status/motivos.
        Garante paridade com os cards da EmployeesPage.
        """
        query = select(ProductionTimeSlice).where(
            ProductionTimeSlice.vehicle_id == vehicle_id,
            ProductionTimeSlice.start_time >= start_date,
            ProductionTimeSlice.start_time <= end_date
        )
        slices = (await db.execute(query)).scalars().all()
        
        run_sec, maint_sec, planned_sec, idle_sec = 0.0, 0.0, 0.0, 0.0

        for s in slices:
            # Recorte temporal para o período
            s_start = max(s.start_time, start_date)
            s_end = min(s.end_time or datetime.now(), end_date)
            duration = (s_end - s_start).total_seconds()
            if duration <= 0: continue

            reason_upper = (s.reason or "").upper()
            cat = (s.category or "").upper()

            # LÓGICA UNIFICADA (Idêntica ao cockpit/dashboard)
            if cat == "PRODUCING" or any(x in reason_upper for x in ["RUNNING", "OPERATION", "EM OPERAÇÃO", "EM USO"]):
                run_sec += duration
            elif cat == "PLANNED_STOP" or any(x in reason_upper for x in ["SETUP", "EM SETUP", "PREPARAÇÃO"]):
                planned_sec += duration
            elif cat == "MAINTENANCE" or any(x in reason_upper for x in ["MANUTENÇÃO", "QUEBRA", "CONSERTO"]):
                maint_sec += duration
            else:
                idle_sec += duration

        total_sec = run_sec + maint_sec + planned_sec + idle_sec
        
        # Disponibilidade OEE = Tempo Produzindo / (Tempo Total - Paradas Planejadas)
        operating_time = total_sec - planned_sec
        availability = (run_sec / operating_time * 100) if operating_time > 0 else 0.0
        
        return {
            "oee_percentage": round(availability, 2), # Simplificado para sua visão
            "availability": round(availability, 2),
            "performance": 100.0,
            "quality": 100.0,
            "metrics": {
                "total_time_min": total_sec / 60,
                "planned_stop_min": planned_sec / 60,
                "producing_min": run_sec / 60
            }
        }