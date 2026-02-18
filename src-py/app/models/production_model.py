from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, JSON
from sqlalchemy.orm import relationship
from typing import Optional, List
from app.db.base_class import Base

class EmployeeDailyMetric(Base):
    """
    Tabela de Fechamento Diário.
    Armazena o desempenho consolidado do operador em um dia específico.
    """
    __tablename__ = "employee_daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # [CORREÇÃO] Removemos a ForeignKey para evitar erro de 'table not found' na inicialização.
    # O ID será salvo normalmente, e o relacionamento via 'relationship' abaixo funciona igual.
    user_id = Column(Integer, nullable=False)
    
    # Já havíamos removido a FK daqui também:
    organization_id = Column(Integer, nullable=False)
    
    # Métricas Consolidadas (Snapshot)
    total_hours = Column(Float, default=0.0)
    productive_hours = Column(Float, default=0.0)
    unproductive_hours = Column(Float, default=0.0)
    efficiency = Column(Float, default=0.0)
    
    # Detalhes Ricos (JSON)
    top_reasons_snapshot = Column(JSON, default=[]) 
    
    # Metadados de Auditoria
    closed_at = Column(DateTime, default=datetime.now)
    version = Column(String, default="v1")

    # Relacionamento com User (Isso funciona pois usa string "User" e é resolvido depois)
    # primaryjoin ajuda o SQLAlchemy a saber como ligar as tabelas sem a ForeignKey explícita na coluna
    user = relationship("User", primaryjoin="foreign(EmployeeDailyMetric.user_id) == User.id")

class VehicleDailyMetric(Base):
    """
    Snapshot Diário de Performance da Máquina.
    """
    __tablename__ = "vehicle_daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    micro_stop_hours = Column(Float, default=0.0)
    mtbf = Column(Float, default=0.0)
    mttr = Column(Float, default=0.0)
    # Sem ForeignKey explícita para evitar conflito de importação
    vehicle_id = Column(Integer, nullable=False)
    organization_id = Column(Integer, nullable=False)
    
    # KPIs
    total_hours = Column(Float, default=0.0)       # 24h ou tempo de turno
    running_hours = Column(Float, default=0.0)     # Produzindo
    idle_hours = Column(Float, default=0.0)        # Parada sem justificativa
    maintenance_hours = Column(Float, default=0.0) # Quebrada/Manutenção
    planned_stop_hours = Column(Float, default=0.0) # Setup, Almoço
    
    # Indicadores Calculados
    availability = Column(Float, default=0.0) # (Run / (Total - Planned))
    utilization = Column(Float, default=0.0)  # (Run / Total)
    
    # Detalhes
    top_reasons_snapshot = Column(JSON, default=[]) # JSON
    
    closed_at = Column(DateTime, default=datetime.now)

    # Relacionamento Lazy
    vehicle = relationship("Vehicle", primaryjoin="foreign(VehicleDailyMetric.vehicle_id) == Vehicle.id")

class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    part_name: Mapped[str] = mapped_column(String(100), nullable=False)
    part_image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    target_quantity: Mapped[int] = mapped_column(Integer, default=0)
    produced_quantity: Mapped[int] = mapped_column(Integer, default=0)
    scrap_quantity: Mapped[int] = mapped_column(Integer, default=0)
    
    status: Mapped[str] = mapped_column(String(20), default="PENDING") # PENDING, SETUP, RUNNING, PAUSED, COMPLETED
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    logs: Mapped[List["ProductionLog"]] = relationship("ProductionLog", back_populates="order")
    sessions: Mapped[List["ProductionSession"]] = relationship("ProductionSession", back_populates="order")
    
    # NOVO: Relacionamento com Fatias de Tempo (Para cálculo exato de custo por O.P.)
    time_slices: Mapped[List["ProductionTimeSlice"]] = relationship("ProductionTimeSlice", back_populates="order")

class ProductionSession(Base):
    __tablename__ = "production_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    production_order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_orders.id"), nullable=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Totais consolidados
    total_produced: Mapped[int] = mapped_column(Integer, default=0)
    total_scrap: Mapped[int] = mapped_column(Integer, default=0)
    
    # Tempos Calculados (em segundos) - Mantidos para retrocompatibilidade rápida
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)      
    productive_seconds: Mapped[int] = mapped_column(Integer, default=0)    
    unproductive_seconds: Mapped[int] = mapped_column(Integer, default=0)  
    
    # Relacionamentos
    vehicle = relationship("Vehicle")
    user = relationship("User")
    order: Mapped["ProductionOrder"] = relationship("ProductionOrder", back_populates="sessions")
    
    logs: Mapped[List["ProductionLog"]] = relationship("ProductionLog", back_populates="session")
    
    # NOVO: Relacionamento com Fatias de Tempo da Sessão
    time_slices: Mapped[List["ProductionTimeSlice"]] = relationship("ProductionTimeSlice", back_populates="session")

class ProductionTimeSlice(Base):
    """
    Tabela MES Central: Armazena intervalos de tempo contínuos em um determinado estado.
    Ex: 
    - 08:00 as 08:30 -> PRODUCING (30 min)
    - 08:30 as 08:45 -> STOPPED (Reason: Troca Ferramenta) (15 min)
    """
    __tablename__ = "production_time_slices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False)
    session_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_sessions.id"), nullable=True)
    order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_orders.id"), nullable=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Categorias Macro: PRODUCING, PLANNED_STOP (Setup, Almoço), UNPLANNED_STOP (Quebra), IDLE
    category: Mapped[str] = mapped_column(String(50), nullable=False) 
    
    # Motivo Detalhado: "Ajuste de Máquina", "Falta de Material", etc.
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Flag auxiliar para cálculo rápido de OEE (Se True, conta para Disponibilidade)
    is_productive: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relacionamentos
    vehicle = relationship("Vehicle")
    session = relationship("ProductionSession", back_populates="time_slices")
    order = relationship("ProductionOrder", back_populates="time_slices")

class ProductionLog(Base):
    __tablename__ = "production_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Máquina (Obrigatório)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False)
    
    # --- MUDANÇAS AQUI ---
    # 1. ID real do usuário (Para o Link funcionar)
    operator_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 2. Crachá usado no momento (Para histórico)
    operator_badge: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 3. Nome do operador no momento (Snapshot para relatórios rápidos)
    operator_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # ---------------------

    session_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_sessions.id"), nullable=True)
    order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_orders.id"), nullable=True)
    
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    new_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relacionamentos
    session: Mapped["ProductionSession"] = relationship("ProductionSession", back_populates="logs")
    order: Mapped["ProductionOrder"] = relationship("ProductionOrder")
    
    # Relacionamento Opcional com User (para pegar foto, e-mail, etc se precisar)
    operator: Mapped["User"] = relationship("User")

class AndonAlert(Base):
    __tablename__ = "andon_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False)
    operator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    sector: Mapped[str] = mapped_column(String(50), nullable=False) # Mecânica, Elétrica...
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="OPEN") # OPEN, IN_PROGRESS, RESOLVED
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    vehicle = relationship("Vehicle", back_populates="andon_alerts")
    operator = relationship("User")

class ProductionAppointment(Base):
    """
    Registra os apontamentos oficiais de produção/parada.
    Estes são os registros que compõem o histórico do operador e são enviados ao SAP.
    """
    __tablename__ = "production_appointments"

    id = Column(Integer, primary_key=True, index=True)
    
    # Vínculos
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    # Armazenamos o CRACHÁ (String) ou ID do usuário, conforme sua lógica de negócio
    operator_id = Column(String(50), index=True, nullable=False) 
    
    # Dados da Ordem
    op_number = Column(String(50), index=True)
    position = Column(String(10), nullable=True) # Etapa/Operação (Ex: 010)
    operation_code = Column(String(20), nullable=True)
    
    # Tempos
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Quantidades (Se houver)
    produced_qty = Column(Float, default=0.0)
    scrap_qty = Column(Float, default=0.0)
    target_qty = Column(Float, default=0.0) # Meta esperada para o período (para cálculo de eficiência)
    
    # Tipificação
    appointment_type = Column(String(20), default="PRODUCTION") # PRODUCTION, STOP, SETUP
    stop_reason = Column(String(255), nullable=True) # Se for parada
    
    # Status de Sincronização SAP
    sap_status = Column(String(20), default="PENDING") # PENDING, SENT, ERROR, NOT_REQUIRED
    sap_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)

    # Relacionamentos
    vehicle = relationship("Vehicle")
    
