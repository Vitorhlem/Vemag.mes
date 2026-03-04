import type { User } from './auth-models';
import type { Machine as Machine } from './machine-models';
import type { InventoryItemStatus } from './inventory-item-models';
import type { MachineComponent } from './machine-component-models';

export enum MaintenanceStatus {
  PENDENTE = 'PENDENTE',
  APROVADA = 'APROVADA',
  REJEITADA = 'REJEITADA',
  EM_ANDAMENTO = 'EM ANDAMENTO',
  CONCLUIDA = 'CONCLUIDA',
}

export enum MaintenanceCategory {
  MECHANICAL = 'Mecânica',
  ELECTRICAL = 'Elétrica',  
  HYDRAULIC = 'Hidráulica',  
  PNEUMATIC = 'Pneumática',  
  BODYWORK = 'Funilaria',
  OTHER = 'Outro'
}

export interface MaintenanceComment {
  id: number;
  comment_text: string;
  file_url: string | null;
  created_at: string;
  user: User | null;
}

export interface ReplaceComponentPayload {
  component_to_remove_id: number;
  new_item_id: number;
  old_item_status: InventoryItemStatus;
  notes?: string | null;
}

export interface InstallComponentPayload {
  new_item_id: number;
  notes?: string | null;
}

export interface MaintenancePartChangePublic {
  id: number;
  timestamp: string;
  user: User;
  notes: string | null;
  component_removed: MachineComponent | null;
  component_installed: MachineComponent;
  is_reverted: boolean;
}

export interface ReplaceComponentResponse {
  success: boolean;
  message: string;
  part_change_log: MaintenancePartChangePublic;
  new_comment: MaintenanceComment;
}

export interface InstallComponentResponse {
  success: boolean;
  message: string;
  part_change_log: MaintenancePartChangePublic;
  new_comment: MaintenanceComment;
}

export interface MaintenanceServiceItem {
  id: number;
  description: string;
  cost: number;
  provider_name?: string | null;
  notes?: string | null;
  created_at: string;
  item_type: string; 
}

export interface MaintenanceServiceItemCreate {
  description: string;
  cost: number;
  provider_name?: string | null;
  notes?: string | null;
  item_type: string;
}

export interface MaintenanceRequest {
  id: number;
  problem_description: string;
  status: MaintenanceStatus;
  category: MaintenanceCategory;
  reporter: User | null;
  machine: Machine;
  approver: User | null;
  manager_notes: string | null;
  created_at: string;
  updated_at: string | null;
  comments: MaintenanceComment[];
  part_changes: MaintenancePartChangePublic[];
  maintenance_type: 'PREVENTIVA' | 'CORRETIVA'; 
  services: MaintenanceServiceItem[];
}

export interface MaintenanceRequestCreate {
  machine_id: number;
  problem_description: string;
  category: MaintenanceCategory;
  maintenance_type?: 'PREVENTIVA' | 'CORRETIVA';
}

export interface MaintenanceRequestUpdate {
  status: MaintenanceStatus;
  manager_notes?: string | null;
  next_maintenance_date?: string | null; 
  next_maintenance_km?: number | null;
}

export interface MaintenanceCommentCreate {
  comment_text: string;
  file_url?: string | null;
}