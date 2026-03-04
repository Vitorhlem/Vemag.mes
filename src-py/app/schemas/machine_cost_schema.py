from pydantic import BaseModel
from datetime import date
from typing import Optional

from app.models.machine_cost_model import CostType

class MachineCostBase(BaseModel):
    description: str
    amount: float
    date: date
    cost_type: CostType

class MachineCostCreate(MachineCostBase):
    """Schema para criar um custo (usado pelo endpoint de Custos)."""
    pass

class MachineCostPublic(MachineCostBase):
    """Schema para retornar um custo (usado em FinePublic)."""
    id: int
    machine_id: int

    class Config:
        from_attributes = True