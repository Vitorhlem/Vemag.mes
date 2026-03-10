import enum
from typing import TYPE_CHECKING, List, Optional
from datetime import date
from sqlalchemy import Column, Integer, String, Date, Text, Float, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base

if TYPE_CHECKING:
    from .organization_model import Organization
    from .maintenance_model import MaintenanceRequest
    from .machine_cost_model import MachineCost
    from .document_model import Document
    from .machine_component_model import MachineComponent
    from .inventory_transaction_model import InventoryTransaction
    from .andon_model import AndonCall

class MachineStatus(str, enum.Enum):
    AVAILABLE = "Disponível"
    IN_USE = "Em uso"
    IN_USE_AUTONOMOUS = "Produção Autônoma"
    SETUP = "Setup"
    MAINTENANCE = "Em manutenção"
    STOPPED = "Parada"
    

class Machine(Base):
    __tablename__ = "machines" 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    andon_alerts: Mapped[List["AndonCall"]] = relationship("AndonCall", back_populates="machine", cascade="all, delete-orphan")
    identifier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sap_resource_code = Column(String, nullable=True)
    layout_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    layout_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[MachineStatus] = mapped_column(SAEnum(MachineStatus), nullable=False, default=MachineStatus.AVAILABLE)
    telemetry_device_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    next_maintenance_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    maintenance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Relações
    organization: Mapped["Organization"] = relationship("Organization", back_populates="machines")
    maintenance_requests: Mapped[List["MaintenanceRequest"]] = relationship("MaintenanceRequest", back_populates="machine", cascade="all, delete-orphan")
    costs: Mapped[List["MachineCost"]] = relationship("MachineCost", back_populates="machine", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="machine", cascade="all, delete-orphan")
    components: Mapped[List["MachineComponent"]] = relationship("MachineComponent", back_populates="machine", cascade="all, delete-orphan")
    inventory_transactions: Mapped[List["InventoryTransaction"]] = relationship("InventoryTransaction", back_populates="related_machine")

    __table_args__ = (
        UniqueConstraint('identifier', 'organization_id', name='_machine_license_org_uc'),
        UniqueConstraint('identifier', 'organization_id', name='_machine_identifier_org_uc'),
    )