import type { Part } from './part-models';
import type { InventoryTransaction } from './inventory-transaction-models';
import type { InventoryItem } from './inventory-item-models';

export interface MachineComponent {
  id: number;
  installation_date: string; 
  uninstallation_date: string | null;
  is_active: boolean;
  part: Part;
  inventory_transaction?: InventoryTransaction;
  item: InventoryItem | null;
}

export interface MachineComponentCreate {
  part_id: number;
  quantity: number;
}