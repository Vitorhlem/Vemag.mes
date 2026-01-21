// Arquivo: src-client/src/services/production-service.ts

import { api } from 'boot/axios';

// --- INTERFACES ---

export interface MachineStats {
  date: string;
  formatted_running_operator: string;
  formatted_running_autonomous: string;
  formatted_paused_operator: string;
  formatted_maintenance: string;
  total_running_operator_seconds: number;
  total_running_autonomous_seconds: number;
  total_paused_operator_seconds: number;
  total_maintenance_seconds: number;
  total_idle_seconds: number;
}

export interface AppointmentPayload {
  op_number: string;
  position: string;
  operation: string;
  operation_desc: string;
  part_description: string;
  item_code: string;
  service_code: string;
  resource_code: string;
  resource_name: string;
  operator_name: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  stop_reason?: string;
  stop_description?: string; // Novo campo
  vehicle_id: number;
}

// --- CLASSE DO SERVIÇO ---

export class ProductionService {
  
  static async getOpenOrders() {
    // CORREÇÃO: Ajustado para a rota correta do Backend (/production/orders/open)
    try {
        const response = await api.get('/production/orders/open'); 
        return response.data;
    } catch (e) {
        console.warn("Erro ao buscar ordens do SAP:", e);
        return [];
    }
  }

  static async sendAppointment(payload: AppointmentPayload) {
    // CORREÇÃO: A rota correta no backend é '/appoint' e não '/appointment'
    const response = await api.post('/production/appoint', payload);
    return response.data;
  }

  // --- O MÉTODO NOVO DEVE FICAR AQUI, DENTRO DA CLASSE ---
  static async getMachineStats(machineId: number, date?: string): Promise<MachineStats> {
    const params = date ? { target_date: date } : {};
    const response = await api.get(`/production/stats/${machineId}`, { params });
    return response.data;
  }

} 
// <-- A CHAVE DA CLASSE FECHA AQUI