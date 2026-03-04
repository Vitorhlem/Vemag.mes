import type { Part } from './part-models';
import type { InventoryTransaction } from './inventory-transaction-models';
import type { Machine } from './machine-models';

export enum InventoryItemStatus {
  DISPONIVEL = "Disponível",
  EM_USO = "Em uso",
  FIM_DE_VIDA = "Fim de Vida",
  EM_MANUTENCAO = 'Em Manutenção',
}

export interface InventoryItem {
  id: number;
  item_identifier: number;
  status: InventoryItemStatus;
  part_id: number;
  installed_on_machine_id: number | null;
  created_at: string;
  installed_at: string | null;
  part: Part | null; 
}

export interface InventoryItemDetails extends InventoryItem {
  part: Part; 
  transactions: InventoryTransaction[];
}

export interface InventoryItemRow extends InventoryItem {
  part: Part; 
  installed_on_machine: Machine | null; 
}

export interface InventoryItemPage {
  total: number;
  items: InventoryItemRow[];
}