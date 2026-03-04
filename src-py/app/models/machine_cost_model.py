import enum
from typing import TYPE_CHECKING, Optional
from datetime import date
from sqlalchemy import Column, Integer, String, Date as SADate, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base

if TYPE_CHECKING:
    from .machine_model import Machine

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

class MachineCost(Base):
    __tablename__ = "machine_costs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(SADate, nullable=False)
    
    # O SAEnum vai validar se a string recebida está na classe CostType acima
    cost_type: Mapped[CostType] = mapped_column(SAEnum(CostType), nullable=False)
    
    machine_id: Mapped[int] = mapped_column(Integer, ForeignKey("machines.id"), nullable=False)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=False)

    machine: Mapped["Machine"] = relationship("Machine", back_populates="costs")
    
