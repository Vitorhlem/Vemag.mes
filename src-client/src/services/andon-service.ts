import { api } from 'boot/axios';

export enum AndonStatus {
  OPEN = 'OPEN',
  IN_PROGRESS = 'IN_PROGRESS',
  RESOLVED = 'RESOLVED'
}

export enum AndonSector {
  MAINTENANCE = 'Manutenção',
  QUALITY = 'Qualidade',
  PCP = 'PCP',
  MANAGER = 'Gerente',
  LOGISTICS = 'Logística',
  SECURITY = 'Segurança'
}

export interface AndonCall {
  id: number;
  machine_id: number;
  machine_name: string;
  machine_sector: string;
  sector: AndonSector;
  reason: string;
  description?: string;
  status: AndonStatus;
  opened_at: string;
  accepted_at?: string;
  accepted_by_name?: string;
}

export interface AndonCallCreate {
  machine_id: number;
  sector: string;
  reason: string;
  description?: string;
}

// --- MUDANÇA AQUI: export const (Nomeado) ---
export const AndonService = {
  async createCall(data: AndonCallCreate): Promise<AndonCall> {
    const response = await api.post<AndonCall>('/andon/', data);
    return response.data;
  },

  async getActiveCalls(): Promise<AndonCall[]> {
    const response = await api.get<AndonCall[]>('/andon/active');
    return response.data;
  },

  async acceptCall(id: number): Promise<AndonCall> {
    const response = await api.put<AndonCall>(`/andon/${id}/accept`);
    return response.data;
  },

  async resolveCall(id: number): Promise<AndonCall> {
    const response = await api.put<AndonCall>(`/andon/${id}/resolve`);
    return response.data;
  }
};