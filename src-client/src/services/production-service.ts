// Arquivo: src-client/src/services/production-service.ts

import { api } from 'boot/axios';
import { db } from 'src/db/offline-db';
import { Notify } from 'quasar';
// --- INTERFACES ---

export interface MachineStats {
  date: string;
  formatted_running_operator: string;
  formatted_running_autonomous: string;
  formatted_pause: string;          // <--- ALTERADO (Removido _operator)
  formatted_setup: string;          // <--- ADICIONADO
  formatted_maintenance: string;
  total_running_operator_seconds: number;
  total_running_autonomous_seconds: number;
  total_pause_seconds: number;      // <--- ALTERADO
  total_setup_seconds: number;      // <--- ADICIONADO
  total_maintenance_seconds: number;
  total_idle_seconds: number;
}
export interface AppointmentPayload {
  op_number: string;
  position: string;
  operation: string;
  operation_desc: string;
  part_description: string;
  DataSource?: string; // Adicione esta linha
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
// eslint-disable-next-line @typescript-eslint/no-explicit-any
static async sendAppointment(payload: any) {
  try {
    // Tenta o envio em tempo real para o SAP
    // CORREÇÃO: Usando a rota correta '/appoint' conforme solicitado
    const response = await api.post('/production/appoint', payload);
    return response.data;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    // Detecta falha de conexão (Network Error ou Timeout)
    const isNetworkError = !error.response || error.code === 'ECONNABORTED';

    if (isNetworkError) {
      // 1. Salva na "Caixa de Saída" local (IndexedDB)
      await db.sync_queue.add({
        type: 'APPOINTMENT',
        payload: payload,
        timestamp: new Date().toISOString(),
        status: 'pending'
      });

      // 2. Notifica o operador que o trabalho não foi perdido
      Notify.create({ 
        type: 'warning', 
        icon: 'cloud_off',
        message: 'Sem internet! Apontamento salvo no tablet e será enviado automaticamente ao SAP quando a rede voltar.',
        caption: `OP: ${payload.op_number}`,
        timeout: 5000
      });

      // Retorna um objeto simulado para não quebrar o fluxo da página
      return { status: 'offline_queued', local: true };
    }

    // Se o erro foi retornado pelo SERVIDOR (ex: 400 Bad Request), repassa o erro
    throw error;
  }
}
  

  // --- O MÉTODO NOVO DEVE FICAR AQUI, DENTRO DA CLASSE ---
  static async getMachineStats(machineId: number, date?: string): Promise<MachineStats> {
    const params = date ? { target_date: date } : {};
    const response = await api.get(`/production/stats/${machineId}`, { params });
    return response.data;
  }

} 
// <-- A CHAVE DA CLASSE FECHA AQUI