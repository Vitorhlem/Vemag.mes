from pydantic import BaseModel
from datetime import datetime
from typing import Optional 
from .part_schema import PartPublic

# Importar o novo schema simples para evitar ciclo com User/Machine
from .inventory_transaction_schema import TransactionForComponent 

class MachineComponentBase(BaseModel):
    part_id: int
    quantity: int 

class MachineComponentCreate(MachineComponentBase):
    pass

class MachineComponentPublic(BaseModel):
    id: int
    installation_date: datetime
    uninstallation_date: datetime | None
    is_active: bool
    part: PartPublic

    # Usamos TransactionForComponent para evitar recursão infinita
    inventory_transaction: Optional[TransactionForComponent] = None

    class Config:
        from_attributes = True