import enum
import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base_class import Base
from app.core.config import settings

if TYPE_CHECKING:
    from .inventory_transaction_model import InventoryTransaction
    from .maintenance_model import MaintenanceRequest
    from .alert_model import Alert
    from .document_model import Document
    from .organization_model import Organization

def generate_employee_id():
    unique_part = uuid.uuid4().hex[:8]
    return f"TRC-{unique_part}"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    PCP = "pcp"
    QUALITY = "quality"
    LOGISTICS = "logistics"
    MAINTENANCE = "maintenance"
    OPERATOR = "operator"
    DRIVER = "driver" 

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    job_title = Column(String, nullable=True)
    employee_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False, default=generate_employee_id)
    device_token = Column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.OPERATOR)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # --- RELACIONAMENTOS ---
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")

    inventory_transactions_performed: Mapped[List["InventoryTransaction"]] = relationship(
        "InventoryTransaction",
        foreign_keys="[InventoryTransaction.user_id]",
        back_populates="user"
    )

    inventory_transactions_received: Mapped[List["InventoryTransaction"]] = relationship(
        "InventoryTransaction",
        foreign_keys="[InventoryTransaction.related_user_id]",
        back_populates="related_user"
    )

    documents: Mapped[List["Document"]] = relationship("Document", back_populates="driver", cascade="all, delete-orphan")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="driver")
    
    # --- A CORREÇÃO DO ERRO ESTÁ AQUI ---
    # O nome da variável DEVE ser 'reported_requests' porque o maintenance_model aponta para ele
    reported_requests: Mapped[List["MaintenanceRequest"]] = relationship(
        "MaintenanceRequest", 
        foreign_keys="[MaintenanceRequest.reported_by_id]", 
        back_populates="reporter"
    )

    @property
    def is_superuser(self) -> bool:
        return self.email in settings.SUPERUSER_EMAILS

    __table_args__ = (
        UniqueConstraint('employee_id', 'organization_id', name='_user_employee_org_uc'),
    )