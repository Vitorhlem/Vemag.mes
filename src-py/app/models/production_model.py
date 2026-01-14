from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional, List
from app.db.base_class import Base

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
    # O erro ocorria porque 'ProductionLog' não tinha o 'order' para fechar esse back_populates
    logs: Mapped[List["ProductionLog"]] = relationship("ProductionLog", back_populates="order")
    sessions: Mapped[List["ProductionSession"]] = relationship("ProductionSession", back_populates="order")

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
    
    # Tempos Calculados (em segundos)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)      
    productive_seconds: Mapped[int] = mapped_column(Integer, default=0)    
    unproductive_seconds: Mapped[int] = mapped_column(Integer, default=0)  
    
    # Relacionamentos
    vehicle = relationship("Vehicle")
    user = relationship("User")
    
    # Correção: Adicionado back_populates para ProductionOrder
    order: Mapped["ProductionOrder"] = relationship("ProductionOrder", back_populates="sessions")
    
    logs: Mapped[List["ProductionLog"]] = relationship("ProductionLog", back_populates="session")

class ProductionLog(Base):
    __tablename__ = "production_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False)
    operator_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
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
    
    # CORREÇÃO DO ERRO: Adicionada a propriedade 'order' que faltava
    order: Mapped["ProductionOrder"] = relationship("ProductionOrder", back_populates="logs")

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