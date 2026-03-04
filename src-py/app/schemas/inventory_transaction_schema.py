from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models.inventory_transaction_model import TransactionType

# --- 1. IMPORTAR OS SCHEMAS QUE SÃO SEGUROS (sem import circular) ---
from .user_schema import UserPublic

# --- 2. Schema para criar uma nova transação ---
class TransactionCreate(BaseModel):
    transaction_type: TransactionType
    quantity: int 
    notes: Optional[str] = None
    related_machine_id: Optional[int] = None
    related_user_id: Optional[int] = None

# --- 3. Schema de Resposta com 'Forward References' ---
class TransactionPublic(BaseModel):
    id: int
    transaction_type: TransactionType
    notes: Optional[str]
    timestamp: datetime
    
    user: Optional[UserPublic] = None
    
    # --- A CORREÇÃO ESTÁ AQUI (Mudei de 'machine' para 'MachinePublic') ---
    related_machine: Optional['MachinePublic'] = None
    
    related_user: Optional[UserPublic] = None
    
    # Usamos strings 'InventoryItemPublic' e 'PartPublic'
    item: Optional['InventoryItemPublic'] = None 
    
    part: Optional['PartListPublic'] = Field(None, alias="part_template")
    
    class Config:
        from_attributes = True

# --- 4. NOVO SCHEMA SIMPLIFICADO ---
class TransactionForComponent(BaseModel):
    id: int
    user: Optional[UserPublic] = None 
    item: Optional['InventoryItemPublic'] = None 

    class Config:
        from_attributes = True

# --- 5. CORREÇÃO DO IMPORT CIRCULAR: Importar e Reconstruir ---
from .part_schema import InventoryItemPublic, PartPublic, PartListPublic
# Certifica-te que o machine_schema.py tem a classe MachinePublic definida
from .machine_schema import MachinePublic 

TransactionPublic.model_rebuild()
TransactionForComponent.model_rebuild()