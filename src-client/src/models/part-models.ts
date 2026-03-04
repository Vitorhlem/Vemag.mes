import type { InventoryItem } from './inventory-item-models';

export type PartCategory = 'Peça' | 'Fluído' | 'Consumível' | 'Ferramenta' | 'EPI' | 'Outro';

export interface Part {
  id: number;
  name: string;
  category: PartCategory;
  part_number: string | null;
  serial_number: string | null; 
  brand: string | null;
  stock: number; 
  minimum_stock: number;
  location: string | null;
  notes: string | null;
  photo_url: string | null;
  value: number | null; 
  invoice_url: string | null;
  items: InventoryItem[]; 
}

export interface PartCreate extends Omit<Part, 'id' | 'stock' | 'items'> {
  initial_quantity?: number; 
}

export type PartUpdate = Partial<Omit<PartCreate, 'initial_quantity'>>;