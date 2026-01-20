// CORREÇÃO: Os valores agora batem com o que o Python espera ('Disponível', etc.)
export enum VehicleStatus {
  AVAILABLE = 'Disponível',
  IN_USE = 'Em uso',
  MAINTENANCE = 'Em manutenção',
}

export interface Vehicle {
  id: number;
  brand: string;
  model: string;
  year: number;
  status: VehicleStatus;
  photo_url?: string | null;
  license_plate?: string | null;
  identifier?: string | null;
  sap_resource_code?: string | null; // <--- Adicione | null para flexibilidade
  telemetry_device_id?: string | null;
  current_km: number;
  current_engine_hours?: number | null;
  last_latitude?: number | null;
  last_longitude?: number | null;
  next_maintenance_date?: string | null;
  next_maintenance_km?: number | null;
  maintenance_notes?: string | null;
  axle_configuration?: string | null;
}

export interface VehicleCreate {
  brand: string;
  model: string;
  year: number;
  license_plate?: string | null;
  identifier?: string | null;
  sap_resource_code?: string; // Ex: 4.02.01
  status: VehicleStatus;
  current_km: number;
  current_engine_hours?: number | null;
  telemetry_device_id?: string | null;
}

export interface VehicleUpdate {
  brand?: string;
  model?: string;
  year?: number;
  license_plate?: string | null;
  identifier?: string | null;
  sap_resource_code?: string; // <--- Adicione
  status?: VehicleStatus;
  current_km?: number;
  current_engine_hours?: number | null;
  telemetry_device_id?: string | null;
}