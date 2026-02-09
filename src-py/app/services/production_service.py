from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from datetime import datetime, date
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
        Calcula e salva o desempenho das MÁQUINAS.
        """
        print(f"🚜 [CRON] Consolidando Máquinas para: {target_date}")
        
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        # 1. Busca máquinas ativas (que tiveram logs ou estão cadastradas)
        # Para simplificar, pegamos todas as máquinas da frota
        # Importe Vehicle dentro do método para evitar ciclo se necessário, ou use select direto
        from app.models.vehicle_model import Vehicle
        machines = (await db.execute(select(Vehicle))).scalars().all()
        
        count = 0
        for machine in machines:
            # 2. Calcula métricas baseadas em TIME SLICES (Mais preciso para máquina)
            # Precisamos das fatias que tocaram o dia alvo
            q_slices = select(ProductionTimeSlice).where(
                ProductionTimeSlice.vehicle_id == machine.id,
                ProductionTimeSlice.start_time <= end_of_day,
                (ProductionTimeSlice.end_time >= start_of_day) | (ProductionTimeSlice.end_time == None)
            )
            slices = (await db.execute(q_slices)).scalars().all()
            
            run_sec = 0.0
            maint_sec = 0.0
            planned_sec = 0.0
            idle_sec = 0.0
            reasons_map = {}
            
            for s in slices:
                # Recorte do tempo para caber no dia (se a fatia virou a noite)
                s_start = max(s.start_time, start_of_day)
                s_end = min(s.end_time or datetime.now(), end_of_day)
                
                duration = (s_end - s_start).total_seconds()
                if duration <= 0: continue
                
                cat = (s.category or "").upper()
                reason = (s.reason or "").upper()
                
                if cat == "PRODUCING" or cat == "RUNNING":
                    run_sec += duration
                elif cat == "PLANNED_STOP" or "SETUP" in reason:
                    planned_sec += duration
                elif "MAINTENANCE" in cat or "MANUTENÇÃO" in reason:
                    maint_sec += duration
                else:
                    idle_sec += duration
                    # Motivos de ociosidade
                    if duration > 60:
                        lbl = s.reason or "Ocioso"
                        reasons_map[lbl] = reasons_map.get(lbl, 0) + 1

            total_sec = run_sec + maint_sec + planned_sec + idle_sec
            if total_sec == 0: total_sec = 1 # Evitar div/0
            
            # Cálculos OEE Simplificados
            # Disponibilidade = Tempo Rodando / (Tempo Total - Paradas Planejadas)
            available_time = total_sec - planned_sec
            availability = (run_sec / available_time * 100) if available_time > 0 else 0.0
            
            # Utilização = Tempo Rodando / Tempo Total Calendário (24h ou Turno)
            utilization = (run_sec / total_sec * 100)
            
            # Top Motivos
            top_reasons = [{"label": k, "count": v} for k, v in sorted(reasons_map.items(), key=lambda x: x[1], reverse=True)[:3]]

            # 3. Persistir
            q_exist = select(VehicleDailyMetric).where(
                VehicleDailyMetric.date == target_date,
                VehicleDailyMetric.vehicle_id == machine.id
            )
            metric = (await db.execute(q_exist)).scalars().first()
            
            if not metric:
                metric = VehicleDailyMetric(date=target_date, vehicle_id=machine.id, organization_id=1)
                db.add(metric)
            
            metric.total_hours = round(total_sec / 3600, 2)
            metric.running_hours = round(run_sec / 3600, 2)
            metric.maintenance_hours = round(maint_sec / 3600, 2)
            metric.planned_stop_hours = round(planned_sec / 3600, 2)
            metric.idle_hours = round(idle_sec / 3600, 2)
            metric.availability = round(availability, 1)
            metric.utilization = round(utilization, 1)
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
        """Abre uma nova fatia de tempo."""
        # Define flag de produtividade baseada na categoria
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
        await db.commit()
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
    async def handle_event(
        db: AsyncSession, 
        event: ProductionEventCreate
    ) -> Dict[str, Any]:
        """
        Processa um evento bruto vindo do Frontend e gerencia as fatias de tempo.
        Retorna um dicionário com os dados do Log criado.
        """
        timestamp = datetime.now()
        
        # 1. Recuperar Entidades (Máquina, Operador, Ordem, Sessão)
        machine = await db.get(Vehicle, event.machine_id)
        if not machine:
            raise ValueError("Machine not found")

        # Buscar Sessão Ativa
        q_session = select(ProductionSession).where(
            ProductionSession.vehicle_id == machine.id,
            ProductionSession.end_time == None
        )
        session = (await db.execute(q_session)).scalars().first()
        
        # Buscar Ordem (Se código fornecido ou da sessão)
        order = None
        if event.order_code:
            q_order = select(ProductionOrder).where(ProductionOrder.code == event.order_code)
            order = (await db.execute(q_order)).scalars().first()
        elif session and session.production_order_id:
            order = await db.get(ProductionOrder, session.production_order_id)

        # 2. Registrar Log Bruto (Auditoria)
        # Buscar ID do operador pelo crachá (email ou employee_id)
        user = None
        user_id_str = None 

        if event.operator_badge:
            clean_badge = str(event.operator_badge).strip()
            
            # Tenta busca robusta
            from sqlalchemy import or_
            q_user = select(User).where(or_(
                User.employee_id == clean_badge,
                User.email == clean_badge
            ))
            user = (await db.execute(q_user)).scalars().first()
            
            if user:
                user_id_str = str(user.id) 
            else:
                user_id_str = clean_badge

        # Criação do Log com ID tratado
        log = ProductionLog(
            vehicle_id=machine.id,
            operator_id=user_id_str, 
            order_id=order.id if order else None,
            session_id=session.id if session else None,
            event_type=event.event_type,
            new_status=event.new_status,
            previous_status=machine.status, 
            reason=event.reason,
            details=event.details,
            timestamp=timestamp
        )
        db.add(log) 

        # 3. Lógica de Fatias de Tempo (Time Slices)
        status_map_category = {} 
        
        if event.new_status:
            # Mapeamento: Status Frontend -> Categoria TimeSlice (MES)
            status_map_category = {
                "EM OPERAÇÃO": "PRODUCING",
                "RUNNING": "PRODUCING",
                "IN_USE": "PRODUCING",
                
                "MANUTENÇÃO": "PLANNED_STOP", 
                "SETUP": "PLANNED_STOP",
                
                "PARADA": "UNPLANNED_STOP",
                "STOPPED": "UNPLANNED_STOP",
                "PAUSED": "UNPLANNED_STOP",
                
                "IDLE": "IDLE",
                "AVAILABLE": "IDLE"
            }
            
            new_category = status_map_category.get(event.new_status.upper(), "UNKNOWN")
            
            # Refinamento por Motivo
            if event.reason and "ALMOÇO" in event.reason.upper():
                new_category = "PLANNED_STOP"
            
            # Fecha fatia anterior
            await ProductionService.close_current_slice(db, machine.id, timestamp)
            
            # Abre nova fatia
            await ProductionService.open_new_slice(
                db, 
                vehicle_id=machine.id, 
                category=new_category, 
                reason=event.reason,
                session_id=session.id if session else None,
                order_id=order.id if order else None
            )

            # 4. Atualizar Status "Visual" da Máquina
            enum_map = {
                "PRODUCING": VehicleStatus.IN_USE,
                "PLANNED_STOP": VehicleStatus.MAINTENANCE,
                "UNPLANNED_STOP": VehicleStatus.STOPPED, 
                "IDLE": VehicleStatus.AVAILABLE
            }
            
            if new_category == "UNPLANNED_STOP" and event.reason and "QUEBRA" in str(event.reason).upper():
                 machine.status = VehicleStatus.MAINTENANCE
            else:
                 machine.status = enum_map.get(new_category, VehicleStatus.AVAILABLE)
            
            db.add(machine)

        # 5. Atualizar Contadores da O.P.
        if event.event_type == 'COUNT' and order:
            order.produced_quantity += (event.quantity_good or 0)
            order.scrap_quantity += (event.quantity_scrap or 0)
            db.add(order)
            
            if session:
                session.total_produced += (event.quantity_good or 0)
                session.total_scrap += (event.quantity_scrap or 0)
                db.add(session)

        # FINALIZAÇÃO
        await db.commit() 
        await db.refresh(log) 

        # [REMOVIDO] consolidate_daily_metrics retirado para evitar conflito de tipos
        
        return {
            "id": log.id, 
            "status": "processed", 
            "operator_id": log.operator_id,
            "operator_name": user.full_name if user else "Desconhecido",
            "new_category": status_map_category.get(str(event.new_status).upper()) if event.new_status else None
        }
    @staticmethod
    async def calculate_oee(db: AsyncSession, vehicle_id: int, start_date: datetime, end_date: datetime):
        """
        Calcula OEE baseado nas Fatias de Tempo (Time Slices).
        Disponibilidade = Tempo Produzindo / (Tempo Total - Paradas Planejadas)
        """
        # Buscar todas as fatias no período
        query = select(ProductionTimeSlice).where(
            ProductionTimeSlice.vehicle_id == vehicle_id,
            ProductionTimeSlice.start_time >= start_date,
            ProductionTimeSlice.start_time <= end_date,
            ProductionTimeSlice.duration_seconds > 0 # Só fatias fechadas
        )
        slices = (await db.execute(query)).scalars().all()
        
        total_time = sum(s.duration_seconds for s in slices)
        planned_stop_time = sum(s.duration_seconds for s in slices if s.category == "PLANNED_STOP")
        producing_time = sum(s.duration_seconds for s in slices if s.category == "PRODUCING")
        
        # 1. Disponibilidade
        operating_time = total_time - planned_stop_time
        availability = (producing_time / operating_time) if operating_time > 0 else 0
        
        # 2. Performance e Qualidade requerem dados da O.P. (Quantidade Teórica vs Real)
        # Simplificação: Performance = 100% se não tiver cadastro de ciclo padrão
        performance = 1.0 
        quality = 1.0

        unplanned_stops = [s for s in slices if s.category == "UNPLANNED_STOP"]
        num_failures = len(unplanned_stops)
        total_repair_time = sum(s.duration_seconds for s in unplanned_stops) / 3600 # horas

        operating_time_hours = operating_time / 3600 if operating_time > 0 else 0
        mtbf = (operating_time_hours / num_failures) if num_failures > 0 else operating_time_hours
        mttr = (total_repair_time / num_failures) if num_failures > 0 else 0
    
        return {
            "oee_percentage": round(availability * performance * quality * 100, 2),
            "availability": round(availability * 100, 2),
            "performance": round(performance * 100, 2),
            "quality": round(quality * 100, 2),
            "metrics": {
                "total_time_min": total_time / 60,
                "planned_stop_min": planned_stop_time / 60,
                "producing_min": producing_time / 60
            }
        }