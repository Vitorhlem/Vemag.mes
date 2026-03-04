
export enum ToolsStatus {
  AVAILABLE = 'available',
  IN_USE = 'in_use',
  MAINTENANCE = 'maintenance'
}

export interface Tools {
  id: number;
  name: string;
  brand: string;
  model: string;
  year: number;
  identifier?: string | null;
  type?: string | null;
  status: ToolsStatus; 
  acquisition_date?: string | null;
  acquisition_value?: number | null;
  notes?: string | null;
}

export type ToolsCreate = Omit<Tools, 'id' | 'status'>; 
export type ToolsUpdate = Partial<ToolsCreate & { status: Tools['status'] }>;