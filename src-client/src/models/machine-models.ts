export enum MachineStatus {
  AVAILABLE = 'Disponível',
  IN_USE = 'Em uso',
  MAINTENANCE = 'Em manutenção',
}

export interface Machine {
  id: number;
  brand: string;
  model: string;
  year: number;
  status: MachineStatus;
  photo_url?: string | null;
  identifier?: string | null;
  sap_resource_code?: string | null; 
  last_latitude?: number | null;
  last_longitude?: number | null;
  next_maintenance_date?: string | null;
  maintenance_notes?: string | null;
}

export interface MachineCreate {
  brand: string;
  model: string;
  year: number;
  identifier?: string | null;
  sap_resource_code?: string; 
  status: MachineStatus;
}

export interface MachineUpdate {
  brand?: string;
  model?: string;
  year?: number;
  identifier?: string | null;
  sap_resource_code?: string; 
  status?: MachineStatus;
}