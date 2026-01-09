import enum
from typing import TYPE_CHECKING, Optional
from datetime import date
from sqlalchemy import Column, Integer, String, Date as SADate, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base

if TYPE_CHECKING:
    from .vehicle_model import Vehicle
    from .fine_model import Fine

# Enum Atualizado para incluir termos Industriais/CMMS
class CostType(str, enum.Enum):
    # --- Legados (Manter para não quebrar dados antigos) ---
    MANUTENCAO = "Manutenção"
    COMBUSTIVEL = "Combustível"
    PEDAGIO = "Pedágio"
    SEGURO = "Seguro"
    PNEU = "Pneu"
    PECAS_COMPONENTES = "Peças e Componentes"
    MULTA = "Multa"
    OUTROS = "Outros"
    
    # --- Novos (Industriais) ---
    # Precisam ser EXATAMENTE iguais ao que está no AddCostDialog.vue
    MANUTENCAO_CORRETIVA = "Manutenção Corretiva"
    MANUTENCAO_PREVENTIVA = "Manutenção Preventiva"
    ENERGIA_ELETRICA = "Energia Elétrica"
    PECAS_REPOSICAO = "Peças de Reposição"
    INSUMOS = "Insumos/Consumíveis"
    SERVICOS_TERCEIROS = "Serviços Terceiros"

class VehicleCost(Base):
    __tablename__ = "vehicle_costs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(SADate, nullable=False)
    
    # O SAEnum vai validar se a string recebida está na classe CostType acima
    cost_type: Mapped[CostType] = mapped_column(SAEnum(CostType), nullable=False)
    
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="costs")
    
    fine_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fines.id", ondelete="SET NULL"), nullable=True, unique=True)
    fine: Mapped[Optional["Fine"]] = relationship("Fine", back_populates="cost")