from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, subqueryload 
from sqlalchemy import select
from datetime import datetime, timezone
from typing import List, Optional 

from app.models.part_model import Part, InventoryItem, InventoryItemStatus
from app.models.inventory_transaction_model import InventoryTransaction, TransactionType
from app.models.machine_model import Machine
from app import crud 
from app.models.user_model import User 

from app.models.machine_component_model import MachineComponent
from app.schemas.machine_component_schema import MachineComponentCreate
from . import crud_inventory_transaction as crud_transaction


async def get_component_for_api(db: AsyncSession, *, component_id: int) -> Optional[MachineComponent]:
    """
    Recarrega um componente com todas as relações necessárias
    para o 'response_model' da API.
    """
    stmt = select(MachineComponent).where(MachineComponent.id == component_id).options(
        selectinload(MachineComponent.part).selectinload(Part.items), 
        
        selectinload(MachineComponent.inventory_transaction)
            .selectinload(InventoryTransaction.user)
            .selectinload(User.organization) 
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def install_component(
    db: AsyncSession, 
    *, 
    machine_id: int, 
    user_id: int, 
    organization_id: int, 
    obj_in: MachineComponentCreate,
    notes: Optional[str] = None
) -> MachineComponent:
    """
    Instala um componente usando a lógica de item a item.
    NÃO FAZ COMMIT.
    """
    
    # 1. Verifica se a peça (template) existe.
    part_template = await db.get(Part, obj_in.part_id)
    if not part_template:
        raise ValueError("Peça (template) não encontrada no inventário.")
    
    # 2. Encontra o PRIMEIRO item de inventário DISPONÍVEL
    stmt = select(InventoryItem).where(
        InventoryItem.part_id == obj_in.part_id,
        InventoryItem.status == InventoryItemStatus.DISPONIVEL,
        InventoryItem.organization_id == organization_id
    ).limit(1)
    
    result = await db.execute(stmt)
    item_to_install = result.scalars().first()

    if not item_to_install:
        raise ValueError(f"Estoque insuficiente para '{part_template.name}'. Nenhum item disponível.")

    # 3. Chama a função central 'change_item_status'
    install_notes = f"Instalado no veículo ID {machine_id}"
    if notes:
        install_notes = f"{notes} (Instalado no veículo ID {machine_id})"

    # Esta função (em crud_part.py) JÁ CRIA o MachineComponent
    updated_item = await crud.crud_part.change_item_status(
        db=db,
        item=item_to_install,
        new_status=InventoryItemStatus.EM_USO,
        user_id=user_id,
        machine_id=machine_id,
        notes=install_notes 
    )

    # 4. Encontra o MachineComponent recém-criado pela 'change_item_status'
    stmt_comp = select(MachineComponent).join(
        InventoryTransaction, MachineComponent.inventory_transaction_id == InventoryTransaction.id
    ).where(
        InventoryTransaction.item_id == updated_item.id,
        # --- AQUI ESTÁ A CORREÇÃO ---
        # Trocamos SAIDA_USO por INSTALACAO para bater com a lógica do crud_part.py
        InventoryTransaction.transaction_type == TransactionType.INSTALACAO
        # --- FIM DA CORREÇÃO ---
    ).order_by(InventoryTransaction.timestamp.desc()).limit(1)

    res_comp = await db.execute(stmt_comp)
    new_component = res_comp.scalars().first()
    
    if not new_component:
        # Se chegou aqui, algo muito errado aconteceu no crud_part.py
        raise Exception("Falha ao criar o registro do componente após a instalação.")
    
    # 5. Retorna o componente "sujo" (sem commit) para o endpoint
    return new_component


async def discard_component(
  db: AsyncSession, 
  *, 
  component_id: int, 
  user_id: int, 
  organization_id: int,
  final_status: InventoryItemStatus, 
  notes: Optional[str] = None
) -> MachineComponent:
  """
  Desinstala um componente, lidando com dados normais (EM_USO) 
  e dados corrompidos (FIM_DE_VIDA, etc.).
  NÃO FAZ COMMIT.
  """
  
  # 1. Encontra o MachineComponent e o Item de Inventário associado
  stmt = select(MachineComponent).where(
    MachineComponent.id == component_id
  ).options(
    # --- INÍCIO DA CORREÇÃO ---
    # Encadeamos .options(selectinload(InventoryItem.part))
    # para garantir que o 'part' seja carregado junto com o 'item'.
    selectinload(MachineComponent.inventory_transaction)
      .selectinload(InventoryTransaction.item)
      .options(selectinload(InventoryItem.part)),
    # --- FIM DA CORREÇÃO ---
    selectinload(MachineComponent.machine)
  )
  
  result = await db.execute(stmt)
  db_component = result.scalar_one_or_none()

  if not db_component:
    raise ValueError("Componente não encontrado.")
  
  if db_component.machine.organization_id != organization_id:
    raise ValueError("Componente não pertence à sua organização.")
    
  if not db_component.is_active:
    # Se o componente já está inativo, apenas o retorne.
    return db_component
    
  # 2. Encontra o item de inventário original
  inventory_item = db_component.inventory_transaction.item
  if not inventory_item:
    raise ValueError("Item de inventário original não encontrado para este componente.")

  # 3. Prepara as notas
  discard_notes = f"Removido do veículo ID {db_component.machine_id}"
  if notes:
    discard_notes = f"{notes} ({discard_notes})"

  # 4. Lógica de Verificação (Conserta dados corrompidos do bug antigo)
  def get_val(s):
      return s.value if hasattr(s, 'value') else str(s)

  current_status_val = get_val(inventory_item.status).lower()
  target_status_val = InventoryItemStatus.EM_USO.value.lower()

  if current_status_val == target_status_val:
    # --- Caminho Normal ---
    await crud.crud_part.change_item_status(
      db=db,
      item=inventory_item,
      new_status=final_status,
      user_id=user_id,
      machine_id=db_component.machine_id, 
      notes=discard_notes
    )
  
  elif current_status_val == get_val(final_status).lower():
    # --- Já está no status final ---
    pass
  
  else:
    raise ValueError(
        f"O item '{inventory_item.item_identifier}' não pode ser movido para reparo. "
        f"Status atual: '{get_val(inventory_item.status)}', esperado: '{InventoryItemStatus.EM_USO.value}'."
    )
  # 5. Atualiza o próprio MachineComponent (sempre executa)
  db_component.is_active = False
  db_component.uninstallation_date = datetime.now(timezone.utc)
  db.add(db_component)
  
  await db.flush()
  
  # 6. Retorna o componente
  return db_component


async def get_components_by_machine(db: AsyncSession, *, machine_id: int) -> List[MachineComponent]:
    """
    Busca o histórico de componentes ATIVOS instalados em um veículo.
    """
    stmt = (
        select(MachineComponent)
        .where(
            MachineComponent.machine_id == machine_id,
            MachineComponent.is_active == True
        )
        .options(
            selectinload(MachineComponent.part).selectinload(Part.items),
            
            selectinload(MachineComponent.inventory_transaction)
                .selectinload(InventoryTransaction.user)
                .selectinload(User.organization)
        )
        .order_by(MachineComponent.installation_date.desc())
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()