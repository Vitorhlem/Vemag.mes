import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum, Text, func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class AndonStatus(str, enum.Enum):
    OPEN = "OPEN"             # Chamado aberto, ninguém viu (Pisca na TV)
    IN_PROGRESS = "IN_PROGRESS" # Técnico assumiu (Fica azul na TV)
    RESOLVED = "RESOLVED"     # Resolvido (Sai da TV)

class AndonSector(str, enum.Enum):
    MAINTENANCE = "Manutenção"
    QUALITY = "Qualidade"
    PCP = "PCP"
    MANAGER = "Gerente"
    LOGISTICS = "Logística"
    SECURITY = "Segurança"

class AndonCall(Base):
    __tablename__ = "andon_calls"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Quem chamou e Onde
    machine_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Quem disparou
    
    # Detalhes do Chamado
    sector = Column(SAEnum(AndonSector), nullable=False)
    reason = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    status = Column(SAEnum(AndonStatus), default=AndonStatus.OPEN, nullable=False)
    
    # Ciclo de Vida (SLA)
    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Responsável pela Solução
    accepted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relacionamentos
    machine = relationship("Vehicle")
    operator = relationship("User", foreign_keys=[operator_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_id])
    organization = relationship("Organization")