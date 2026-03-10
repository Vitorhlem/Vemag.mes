
import { api } from 'boot/axios';
import { db } from 'src/db/offline-db';
import { Notify } from 'quasar';
// --- INTERFACES ---

export interface MachineStats {
  date: string;
  formatted_running_operator: string;
  formatted_running_autonomous: string;
  formatted_pause: string;        
  formatted_setup: string;          
  formatted_maintenance: string;
  formatted_idle: string;      
  total_running_operator_seconds: number;
  total_running_autonomous_seconds: number;
  total_pause_seconds: number;     
  total_setup_seconds: number;     
  total_maintenance_seconds: number;
  total_idle_seconds: number;
  formatted_micro_stop: string;
}
export interface AppointmentPayload {
  op_number: string;
  position: string;
  operation: string;
  operation_desc: string;
  part_description: string;
  DataSource?: string; 
  item_code: string;
  service_code: string;
  resource_code: string;
  resource_name: string;
  operator_name: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  stop_reason?: string;
  stop_description?: string;
  machine_id: number;
}

// --- CLASSE DO SERVIÇO ---

export class ProductionService {
  
  static async getOpenOrders() {
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
    const response = await api.post('/production/appoint', payload);
    return response.data;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    const isNetworkError = !error.response || error.code === 'ECONNABORTED';

    if (isNetworkError) {
      await db.sync_queue.add({
        type: 'APPOINTMENT',
        payload: payload,
        timestamp: new Date().toISOString(),
        status: 'pending'
      });

      Notify.create({ 
        type: 'warning', 
        icon: 'cloud_off',
        message: 'Sem internet! Apontamento salvo no tablet e será enviado automaticamente ao SAP quando a rede voltar.',
        caption: `OP: ${payload.op_number}`,
        timeout: 5000
      });

      return { status: 'offline_queued', local: true };
    }

    throw error;
  }
}
  

  static async getMachineStats(machineId: number, date?: string): Promise<MachineStats> {
    const params = date ? { target_date: date } : {};
    const response = await api.get(`/production/stats/${machineId}`, { params });
    return response.data;
  }

} 
