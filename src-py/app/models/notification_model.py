from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class NotificationType(str, enum.Enum):
    MAINTENANCE_DUE_DATE = "maintenance_due_date"
    MAINTENANCE_DUE_KM = "maintenance_due_km"
    DOCUMENT_EXPIRING = "document_expiring"
    LOW_STOCK = "low_stock"
    COST_EXCEEDED = "cost_exceeded"
    
    MAINTENANCE_REQUEST_NEW = "maintenance_request_new"
    MAINTENANCE_REQUEST_STATUS_UPDATE = "maintenance_request_status_update"
    MAINTENANCE_REQUEST_NEW_COMMENT = "maintenance_request_new_comment"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False) # Para qual usuário é o alerta
    
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    notification_type = Column(SAEnum(NotificationType), nullable=False)

    related_entity_type = Column(String, nullable=True)  
    related_entity_id = Column(Integer, nullable=True)

    related_machine_id = Column(Integer, ForeignKey("machines.id", ondelete="CASCADE"), nullable=True)

    user = relationship("User")
    machine = relationship("Machine")
    organization = relationship("Organization")