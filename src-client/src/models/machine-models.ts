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
  license_plate?: string | null;
  identifier?: string | null;
  sap_resource_code?: string | null; 
  current_km: number;
  current_engine_hours?: number | null;
  last_latitude?: number | null;
  last_longitude?: number | null;
  next_maintenance_date?: string | null;
  next_maintenance_km?: number | null;
  maintenance_notes?: string | null;
  axle_configuration?: string | null;
}

export interface MachineCreate {
  brand: string;
  model: string;
  year: number;
  license_plate?: string | null;
  identifier?: string | null;
  sap_resource_code?: string; 
  status: MachineStatus;
  current_km: number;
  current_engine_hours?: number | null;
}

export interface MachineUpdate {
  brand?: string;
  model?: string;
  year?: number;
  license_plate?: string | null;
  identifier?: string | null;
  sap_resource_code?: string; 
  status?: MachineStatus;
  current_km?: number;
  current_engine_hours?: number | null;
}