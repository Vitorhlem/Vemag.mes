import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Date, Float, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base

# Se tiveres imports de Journey aqui, remove-os!

class ToolStatus(str, enum.Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"

class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    brand: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[ToolStatus] = mapped_column(String(20), nullable=False, default=ToolStatus.AVAILABLE)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    identifier: Mapped[str] = mapped_column(String(50), nullable=True) 

    # Novos campos
    acquisition_date: Mapped[Date] = mapped_column(Date, nullable=True)
    acquisition_value: Mapped[Float] = mapped_column(Float, nullable=True)
    notes: Mapped[Text] = mapped_column(Text, nullable=True)

    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # --- CORREÇÃO AQUI ---
    # 1. Mudamos back_populates para "tools" (que é o nome no Organization)
    organization = relationship("Organization", back_populates="tools")

    # 2. REMOVIDA a linha: journeys = relationship("Journey"...)