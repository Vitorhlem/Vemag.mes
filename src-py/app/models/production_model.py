from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, Date, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List
from app.db.base_class import Base

class EmployeeDailyMetric(Base):
    """
    Tabela de Fechamento Diário.
    Armazena o desempenho consolidado do operador em um dia específico.
    """
    __tablename__ = "employee_daily_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    total_hours: Mapped[float] = mapped_column(Float, default=0.0)
    productive_hours: Mapped[float] = mapped_column(Float, default=0.0)
    unproductive_hours: Mapped[float] = mapped_column(Float, default=0.0)
    efficiency: Mapped[float] = mapped_column(Float, default=0.0)
    
    top_reasons_snapshot: Mapped[list] = mapped_column(JSON, default=[]) 
    
    closed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    version: Mapped[str] = mapped_column(String, default="v1")

    user = relationship("User", primaryjoin="foreign(EmployeeDailyMetric.user_id) == User.id")

class MachineDailyMetric(Base):
    """
    Snapshot Diário de Performance da Máquina.
    """
    __tablename__ = "machine_daily_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    
    machine_id: Mapped[int] = mapped_column(Integer, nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    total_hours: Mapped[float] = mapped_column(Float, default=0.0)       
    running_hours: Mapped[float] = mapped_column(Float, default=0.0)     
    idle_hours: Mapped[float] = mapped_column(Float, default=0.0)
    pause_hours: Mapped[float] = mapped_column(Float, default=0.0)        
    maintenance_hours: Mapped[float] = mapped_column(Float, default=0.0) 
    planned_stop_hours: Mapped[float] = mapped_column(Float, default=0.0) 
    micro_stop_hours: Mapped[float] = mapped_column(Float, default=0.0)
    
    availability: Mapped[float] = mapped_column(Float, default=0.0) 
    utilization: Mapped[float] = mapped_column(Float, default=0.0)  
    mtbf: Mapped[float] = mapped_column(Float, default=0.0)
    mttr: Mapped[float] = mapped_column(Float, default=0.0)
    
    top_reasons_snapshot: Mapped[list] = mapped_column(JSON, default=[])
    closed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    machine = relationship("Machine", primaryjoin="foreign(MachineDailyMetric.machine_id) == Machine.id")

class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    part_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    target_quantity: Mapped[int] = mapped_column(Integer, default=0)
    produced_quantity: Mapped[int] = mapped_column(Integer, default=0)
    scrap_quantity: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # A linha "logs" foi removida daqui!
    sessions: Mapped[List["ProductionSession"]] = relationship("ProductionSession", back_populates="order")
    time_slices: Mapped[List["ProductionTimeSlice"]] = relationship("ProductionTimeSlice", back_populates="order")
class ProductionSession(Base):
    __tablename__ = "production_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    machine_id: Mapped[int] = mapped_column(Integer, ForeignKey("machines.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    production_order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_orders.id"), nullable=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    total_produced: Mapped[int] = mapped_column(Integer, default=0)
    total_scrap: Mapped[int] = mapped_column(Integer, default=0)
    
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)      
    productive_seconds: Mapped[int] = mapped_column(Integer, default=0)    
    unproductive_seconds: Mapped[int] = mapped_column(Integer, default=0)  
    
    machine = relationship("Machine")
    user = relationship("User")
    order: Mapped["ProductionOrder"] = relationship("ProductionOrder", back_populates="sessions")
    
    # A linha "logs" foi removida daqui!
    time_slices: Mapped[List["ProductionTimeSlice"]] = relationship("ProductionTimeSlice", back_populates="session")
class ProductionTimeSlice(Base):
    """
    Tabela MES Central: Armazena intervalos de tempo contínuos em um determinado estado.
    OBS: Futuramente esta tabela pode ser mesclada com a ProductionAppointment.
    """
    __tablename__ = "production_time_slices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    machine_id: Mapped[int] = mapped_column(Integer, ForeignKey("machines.id"), nullable=False)
    session_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_sessions.id"), nullable=True)
    order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("production_orders.id"), nullable=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    category: Mapped[str] = mapped_column(String(50), nullable=False) 
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_productive: Mapped[bool] = mapped_column(Boolean, default=False)

    machine = relationship("Machine")
    session = relationship("ProductionSession", back_populates="time_slices")
    order = relationship("ProductionOrder", back_populates="time_slices")

class ProductionLog(Base):
    __tablename__ = "production_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    machine_id: Mapped[int] = mapped_column(Integer, ForeignKey("machines.id"), nullable=False)
    
    operator_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    operator_badge: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    operator_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    new_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 👇 ESTE CAMPO VOLTOU PARA ALIMENTAR A TABELA
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True) 
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    operator: Mapped["User"] = relationship("User")

# =========================================================================================
# O NOVO PRODUCTION APPOINTMENT (RICO E COMPLETO PARA O SAP)
# =========================================================================================
class ProductionAppointment(Base):
    """
    Registra os apontamentos oficiais de produção/parada para o SAP.
    Esta tabela é um espelho exato do payload enviado ao endpoint 'LGO_CAPONTAMENTO'.
    """
    __tablename__ = "production_appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # --- Contexto MES ---
    machine_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("machines.id"), nullable=True)
    operator_badge: Mapped[str] = mapped_column(String(50), index=True, nullable=False) 
    appointment_type: Mapped[str] = mapped_column(String(20), default="PRODUCTION") # PRODUCTION, STOP, SETUP
    
    # --- Tempos (Formato Nativo Banco) ---
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # ---------------------------------------------------------------------
    # ESPELHO DO PAYLOAD SAP (Todos os campos do LGO_CAPONTAMENTO)
    # ---------------------------------------------------------------------
    sap_doc_num: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)         # U_NumeroDocumento (OP ou OS)
    sap_position: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)        # U_Posicao
    sap_operation_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # U_Operacao
    sap_operation_desc: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # U_DescricaoOperacao
    sap_service_desc: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)   # U_DescricaoServico (part_name)
    
    sap_operator_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # U_DescricaoOperador
    operator_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)     # U_Operador (ID limpo)
    
    sap_resource_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # U_Recurso
    sap_resource_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # U_DescricaoRecurso
    
    sap_data_source: Mapped[str] = mapped_column(String(10), default="I")                 # DataSource (I)
    sap_doc_type: Mapped[str] = mapped_column(String(10), default="1")                    # U_TipoDocumento (1=OP, 2=OS/Parada)
    sap_origin: Mapped[str] = mapped_column(String(10), default="S")                      # U_OrigemApontamento (S)
    
    # Tratamento da Regra do U_Servico (Preenchido apenas se for O.S.)
    sap_service_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)   # U_Servico 
    
    # Tratamento de Paradas e Setups
    sap_stop_reason_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)# U_MotivoParada
    sap_stop_reason_desc: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)# U_DescricaoParada
    sap_is_setup: Mapped[str] = mapped_column(String(1), default="N")                     # U_setup (S/N)
    sap_stoppage_apt: Mapped[str] = mapped_column(String(1), default="N")                 # U_AptoParada (S/N)
    
    # ---------------------------------------------------------------------
    # Status de Integração
    # ---------------------------------------------------------------------
    sap_status: Mapped[str] = mapped_column(String(20), default="PENDING")                # PENDING, SENT, ERROR
    sap_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)               # Mensagem de Retorno SAP
    
    # Outros 
    target_qty: Mapped[float] = mapped_column(Float, default=0.0) 

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    machine = relationship("Machine")